import random
from flask import Blueprint, request, jsonify
import mysql.connector
from datetime import datetime, timedelta
from db import get_db_connection

supplier_bp = Blueprint('supplier', __name__)

def get_logged_in_user():
    try:
        with open("logged_in_user.txt", "r") as file:
            return file.read().strip()
    except:
        return None

@supplier_bp.route('/supplier_orders', methods=['GET'])
def get_supplier_orders():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "Not authenticated"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get orders containing supplier's products
        cursor.execute("""
            SELECT o.orderID, o.date as orderDate, c.cName as customerName,
                   p.productID, p.pName as productName, 
                   co.productQuantity as quantity,
                   IF(f.productID IS NULL, 0, 1) as confirmed
            FROM Orders o
            JOIN Customer c ON o.userID = c.userID
            JOIN Contains co ON o.orderID = co.orderID
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON o.orderID = f.orderID AND p.productID = f.productID
            WHERE p.userID = %s
            ORDER BY o.date DESC
        """, (user_id,))
        
        orders_data = cursor.fetchall()
        
        # Group by order
        orders = {}
        for item in orders_data:
            if item['orderID'] not in orders:
                orders[item['orderID']] = {  # Fixed this line - added missing ]
                    'orderID': item['orderID'],
                    'orderDate': item['orderDate'],
                    'customerName': item['customerName'],
                    'products': [],
                    'isFullyConfirmed': True
                }
            
            orders[item['orderID']]['products'].append({
                'id': item['productID'],
                'name': item['productName'],
                'quantity': item['quantity'],
                'confirmed': bool(item['confirmed'])
            })
            
            if not item['confirmed']:
                orders[item['orderID']]['isFullyConfirmed'] = False
        
        return jsonify(list(orders.values()))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/confirm_product', methods=['POST'])
def confirm_product():
    conn = None
    cursor = None
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        order_id = data.get('orderID')
        product_id = data.get('productID')
        
        if not order_id or not product_id:
            return jsonify({"error": "Missing orderID or productID"}), 400

        # Verify user is logged in
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify product ownership
        cursor.execute("""
            SELECT p.productID 
            FROM Product p
            WHERE p.productID = %s AND p.userID = %s
        """, (product_id, user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Product does not belong to you"}), 403

        # 2. Check warehouse stock
        cursor.execute("""
            SELECT s.warehouseID, s.productQuantity
            FROM Storage s
            JOIN Supplies sp ON s.warehouseID = sp.warehouseID
            WHERE s.productID = %s AND sp.userID = %s
        """, (product_id, user_id))
        
        warehouses = cursor.fetchall()
        
        cursor.execute("""
            SELECT productQuantity 
            FROM Contains 
            WHERE orderID = %s AND productID = %s
        """, (order_id, product_id))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Product not found in order"}), 404
        required_quantity = result['productQuantity']
        
        warehouse_id = None
        for warehouse in warehouses:
            if warehouse['productQuantity'] >= required_quantity:
                warehouse_id = warehouse['warehouseID']
                break
        
        if not warehouse_id:
            return jsonify({"error": "Insufficient stock in any warehouse"}), 400

        # 3. Update Fulfill and Storage tables
        cursor.execute("""
            INSERT INTO Fulfill (warehouseID, orderID, productID)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE warehouseID = VALUES(warehouseID)
        """, (warehouse_id, order_id, product_id))

        cursor.execute("""
            UPDATE Storage
            SET productQuantity = productQuantity - %s
            WHERE warehouseID = %s AND productID = %s
        """, (required_quantity, warehouse_id, product_id))

        # 4. Check if all products are confirmed
        cursor.execute("""
            SELECT COUNT(*) as unconfirmed_count
            FROM Contains co
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON co.orderID = f.orderID AND co.productID = f.productID
            WHERE co.orderID = %s AND p.userID = %s AND f.productID IS NULL
        """, (order_id, user_id))
        
        unconfirmed_count = cursor.fetchone()['unconfirmed_count']
        
        conn.commit()
        return jsonify({
            "success": True,
            "message": "Product confirmed successfully",
            "orderStatus": "Fully Confirmed" if unconfirmed_count == 0 else "Partially Confirmed"
        })

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/arrange_transport', methods=['POST'])
def arrange_transport():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        order_id = data.get('orderID')
        vehicle_no = data.get('vehicleNo')
        driver_name = data.get('driverName')
        
        if not order_id or not vehicle_no or not driver_name:
            return jsonify({"error": "Missing required fields"}), 400

        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify order belongs to this supplier and is fully confirmed
        cursor.execute("""
            SELECT COUNT(*) as unconfirmed_count
            FROM Contains co
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON co.orderID = f.orderID AND co.productID = f.productID
            WHERE co.orderID = %s AND p.userID = %s AND f.productID IS NULL
        """, (order_id, user_id))
        
        unconfirmed_count = cursor.fetchone()['unconfirmed_count']
        if unconfirmed_count > 0:
            return jsonify({"error": "Order not fully confirmed"}), 400

        # 2. Generate transport ID
        transport_id = f"TR{random.randint(1000, 9999)}"

        # 3. Insert transport record
        cursor.execute("""
            INSERT INTO Transport (transportID, vehicleNo, driverName, status, orderID)
            VALUES (%s, %s, %s, 'Pending', %s)
        """, (transport_id, vehicle_no, driver_name, order_id))

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Transport arranged successfully",
            "transportID": transport_id
        })

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/get_transport_details/<order_id>', methods=['GET'])
def get_transport_details(order_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT transportID, vehicleNo, driverName, status
            FROM Transport
            WHERE orderID = %s
        """, (order_id,))
        
        transport = cursor.fetchone()
        
        if not transport:
            return jsonify({"error": "No transport arranged for this order"}), 404
            
        return jsonify(transport)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/get_available_transports', methods=['GET'])
def get_available_transports():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT transportID, vehicleNo, driverName 
            FROM Transport 
            WHERE status = 'Available'
        """)
        
        transports = cursor.fetchall()
        return jsonify(transports)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/create_shipment', methods=['POST'])
def create_shipment():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        order_id = data.get('orderID')
        transport_id = data.get('transportID')
        
        if not order_id or not transport_id:
            return jsonify({"error": "Missing orderID or transportID"}), 400

        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify order belongs to this supplier and is fully confirmed
        cursor.execute("""
            SELECT COUNT(*) as unconfirmed_count
            FROM Contains co
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON co.orderID = f.orderID AND co.productID = f.productID
            WHERE co.orderID = %s AND p.userID = %s AND f.productID IS NULL
        """, (order_id, user_id))
        
        unconfirmed_count = cursor.fetchone()['unconfirmed_count']
        if unconfirmed_count > 0:
            return jsonify({"error": "Order not fully confirmed"}), 400

        # Generate shipment ID
        shipment_id = f"SH{random.randint(1000, 9999)}"
        
        # Calculate timestamps
        start_time = datetime.now()
        estimated_delivery = start_time + timedelta(hours=2)
        
        # Create shipment
        cursor.execute("""
            INSERT INTO Shipment (
                shipmentID, transportID, orderID, status, 
                startTime, estimatedDelivery
            ) VALUES (%s, %s, %s, 'In Transit', %s, %s)
        """, (shipment_id, transport_id, order_id, start_time, estimated_delivery))
        
        # Update transport status
        cursor.execute("""
            UPDATE Transport 
            SET status = 'In Transit', orderID = %s
            WHERE transportID = %s
        """, (order_id, transport_id))
        
        # Update order status
        cursor.execute("""
            UPDATE Orders 
            SET shipmentStatus = 'In Transit'
            WHERE orderID = %s
        """, (order_id,))
        
        conn.commit()
        
        return jsonify({
            "success": True,
            "message": "Shipment created successfully",
            "shipmentID": shipment_id,
            "estimatedDelivery": estimated_delivery.strftime("%Y-%m-%d %H:%M:%S")
        })

    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/update_shipment_status', methods=['POST'])
def update_shipment_status():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        order_id = data.get('orderID')
        status = data.get('status')
        
        if not order_id or not status:
            return jsonify({"error": "Missing orderID or status"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Update shipment status
        cursor.execute("""
            UPDATE Shipment 
            SET status = %s
            WHERE orderID = %s
        """, (status, order_id))
        
        # Update transport status
        if status == 'Delivered':
            cursor.execute("""
                UPDATE Transport t
                JOIN Shipment s ON t.transportID = s.transportID
                SET t.status = 'Available', t.orderID = NULL
                WHERE s.orderID = %s
            """, (order_id,))
        
        # Update order status
        cursor.execute("""
            UPDATE Orders 
            SET shipmentStatus = %s
            WHERE orderID = %s
        """, (status, order_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Shipment status updated"})
        
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/check_deliveries', methods=['POST'])
def check_deliveries():
    """Background task to update deliveries that are past their estimated time"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find shipments that should be delivered by now
        cursor.execute("""
            SELECT s.orderID 
            FROM Shipment s
            WHERE s.status = 'In Transit' 
            AND s.estimatedDelivery <= %s
        """, (datetime.now(),))
        
        overdue_shipments = cursor.fetchall()
        
        for shipment in overdue_shipments:
            # Update to delivered status
            cursor.execute("""
                UPDATE Shipment 
                SET status = 'Delivered'
                WHERE orderID = %s
            """, (shipment['orderID'],))
            
            # Update transport status
            cursor.execute("""
                UPDATE Transport t
                JOIN Shipment s ON t.transportID = s.transportID
                SET t.status = 'Available', t.orderID = NULL
                WHERE s.orderID = %s
            """, (shipment['orderID'],))
            
            # Update order status
            cursor.execute("""
                UPDATE Orders 
                SET shipmentStatus = 'Delivered'
                WHERE orderID = %s
            """, (shipment['orderID'],))
        
        conn.commit()
        return jsonify({
            "success": True,
            "updated": len(overdue_shipments)
        })
        
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()