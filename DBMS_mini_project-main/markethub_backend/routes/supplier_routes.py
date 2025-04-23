from flask import Blueprint, request, jsonify
import mysql.connector
from datetime import datetime
from db import get_db_connection

supplier_bp = Blueprint('supplier', __name__)

def get_logged_in_user():
    try:
        with open("logged_in_user.txt", "r") as file:
            return file.read().strip()
    except:
        return None

def generate_new_product_id(cursor):
    cursor.execute("SELECT productID FROM Product ORDER BY productID DESC LIMIT 1")
    result = cursor.fetchone()
    if result:
        last_id = int(result[0][1:])
        new_id = f"P{last_id + 1:03}"
    else:
        new_id = "P001"
    return new_id

@supplier_bp.route('/get_categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT categoryName FROM Category")
        categories = [row[0] for row in cursor.fetchall()]
        return jsonify(categories)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/get_all_warehouses', methods=['GET'])
def get_all_warehouses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT warehouseID, location FROM Warehouse")
        warehouses = cursor.fetchall()
        return jsonify(warehouses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/add_product', methods=['POST'])
def add_product():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        data = request.json
        required_fields = ['pName', 'description', 'price', 'unit', 'categoryName']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        product_id = generate_new_product_id(cursor)
        
        cursor.execute("""
            INSERT INTO Product (productID, pName, description, price, unit, categoryName, userID)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            product_id,
            data['pName'],
            data['description'],
            data['price'],
            data['unit'],
            data['categoryName'],
            user_id
        ))

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Product added successfully",
            "productID": product_id
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

@supplier_bp.route('/my_products', methods=['GET'])
def my_products():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT productID, pName, description, price, unit, categoryName
            FROM Product
            WHERE userID = %s
        """, (user_id,))
        
        products = cursor.fetchall()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/update_stock', methods=['POST'])
def update_stock():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        data = request.json
        required_fields = ['productID', 'warehouseID', 'quantity']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify the product belongs to this supplier
        cursor.execute("SELECT userID FROM Product WHERE productID = %s", (data['productID'],))
        product = cursor.fetchone()
        if not product or product['userID'] != user_id:
            return jsonify({"error": "Product does not belong to you"}), 403

        # 2. Verify the warehouse exists
        cursor.execute("SELECT warehouseID FROM Warehouse WHERE warehouseID = %s", (data['warehouseID'],))
        if not cursor.fetchone():
            return jsonify({"error": "Warehouse does not exist"}), 400

        # 3. Check if quantity is valid
        if int(data['quantity']) <= 0:
            return jsonify({"error": "Quantity must be positive"}), 400

        # 4. Check if expiry date is valid (if provided)
        if data.get('expiryDate'):
            try:
                expiry_date = datetime.strptime(data['expiryDate'], '%Y-%m-%d').date()
                if expiry_date < datetime.now().date():
                    return jsonify({"error": "Expiry date cannot be in the past"}), 400
            except ValueError:
                return jsonify({"error": "Invalid expiry date format"}), 400

        # 5. Check if discount dates are valid (if discount provided)
        if data.get('discountPercentage'):
            try:
                discount_pct = float(data['discountPercentage'])
                if not 0 <= discount_pct <= 100:
                    return jsonify({"error": "Discount must be between 0 and 100%"}), 400
                
                if not data.get('startDate') or not data.get('endDate'):
                    return jsonify({"error": "Discount requires both start and end dates"}), 400
                
                start_date = datetime.strptime(data['startDate'], '%Y-%m-%d').date()
                end_date = datetime.strptime(data['endDate'], '%Y-%m-%d').date()
                
                if start_date > end_date:
                    return jsonify({"error": "Discount start date must be before end date"}), 400
                
                if end_date < datetime.now().date():
                    return jsonify({"error": "Discount end date cannot be in the past"}), 400
            except ValueError:
                return jsonify({"error": "Invalid date format"}), 400

        # 6. Check if stock entry already exists for this product+warehouse
        cursor.execute("""
            SELECT productQuantity FROM Storage 
            WHERE productID = %s AND warehouseID = %s
        """, (data['productID'], data['warehouseID']))
        existing_stock = cursor.fetchone()

        if existing_stock:
            # Update existing stock
            new_quantity = existing_stock['productQuantity'] + int(data['quantity'])
            cursor.execute("""
                UPDATE Storage 
                SET productQuantity = %s
                WHERE productID = %s AND warehouseID = %s
            """, (new_quantity, data['productID'], data['warehouseID']))
        else:
            # Insert new stock entry
            cursor.execute("""
                INSERT INTO Storage (productID, warehouseID, productQuantity)
                VALUES (%s, %s, %s)
            """, (data['productID'], data['warehouseID'], data['quantity']))

        # 7. Update expiry date if provided
        if data.get('expiryDate'):
            cursor.execute("""
                UPDATE Product 
                SET expiryDate = %s 
                WHERE productID = %s
            """, (data['expiryDate'], data['productID']))

        # 8. Handle discount if provided
        if data.get('discountPercentage') and data.get('startDate') and data.get('endDate'):
            # Generate incremental discount ID
            cursor.execute("SELECT discountID FROM Discount ORDER BY discountID DESC LIMIT 1")
            last_discount = cursor.fetchone()
            if last_discount:
                last_num = int(last_discount['discountID'][1:])  # Extract number from D001
                new_id = f"D{last_num + 1:03d}"  # Format as D002, D003, etc.
            else:
                new_id = "D001"
            
            # Remove existing discounts for this product in the same date range
            cursor.execute("""
                DELETE FROM Discount 
                WHERE productID = %s 
                AND (
                    (startDate BETWEEN %s AND %s)
                    OR (endDate BETWEEN %s AND %s)
                    OR (%s BETWEEN startDate AND endDate)
                    OR (%s BETWEEN startDate AND endDate)
                )
            """, (
                data['productID'],
                data['startDate'], data['endDate'],
                data['startDate'], data['endDate'],
                data['startDate'], data['endDate']
            ))
            
            # Add new discount
            cursor.execute("""
                INSERT INTO Discount (discountID, discountPercentage, startDate, endDate, productID)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                new_id,
                data['discountPercentage'],
                data['startDate'],
                data['endDate'],
                data['productID']
            ))

        conn.commit()
        return jsonify({"success": True, "message": "Stock updated successfully"})
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/get_stock_details', methods=['GET'])
def get_stock_details():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all products that belong to this supplier
        cursor.execute("""
            SELECT p.productID, p.pName
            FROM Product p
            WHERE p.userID = %s
        """, (user_id,))
        products = cursor.fetchall()
        
        stock_data = []
        for product in products:
            # Get storage information for this product across all warehouses
            cursor.execute("""
                SELECT s.warehouseID, w.location, s.productQuantity, 
                       p.expiryDate, d.discountPercentage, 
                       d.startDate, d.endDate
                FROM Storage s
                JOIN Warehouse w ON s.warehouseID = w.warehouseID
                JOIN Product p ON s.productID = p.productID
                LEFT JOIN Discount d ON p.productID = d.productID 
                    AND CURDATE() BETWEEN d.startDate AND d.endDate
                WHERE s.productID = %s
            """, (product['productID'],))
            
            storage_items = cursor.fetchall()
            
            if storage_items:
                for item in storage_items:
                    stock_data.append({
                        "productID": product['productID'],
                        "pName": product['pName'],
                        "warehouseID": item['warehouseID'],
                        "location": item['location'],
                        "productQuantity": item['productQuantity'],
                        "expiryDate": item['expiryDate'],
                        "discountPercentage": item['discountPercentage'],
                        "startDate": item['startDate'],
                        "endDate": item['endDate']
                    })
            else:
                # Show product even if not in any warehouse
                cursor.execute("""
                    SELECT p.expiryDate, d.discountPercentage, 
                           d.startDate, d.endDate
                    FROM Product p
                    LEFT JOIN Discount d ON p.productID = d.productID 
                        AND CURDATE() BETWEEN d.startDate AND d.endDate
                    WHERE p.productID = %s
                """, (product['productID'],))
                product_info = cursor.fetchone()
                
                stock_data.append({
                    "productID": product['productID'],
                    "pName": product['pName'],
                    "warehouseID": None,
                    "location": "Not in stock",
                    "productQuantity": 0,
                    "expiryDate": product_info['expiryDate'] if product_info else None,
                    "discountPercentage": product_info['discountPercentage'] if product_info else None,
                    "startDate": product_info['startDate'] if product_info else None,
                    "endDate": product_info['endDate'] if product_info else None
                })
        
        # Clean expired products
        cursor.execute("""
            DELETE FROM Storage
            WHERE productID IN (
                SELECT productID FROM Product 
                WHERE expiryDate IS NOT NULL AND expiryDate < CURDATE()
            )
        """)
        
        conn.commit()
        return jsonify(stock_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/get_pending_orders', methods=['GET'])
def get_pending_orders():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all orders containing products from this supplier
        cursor.execute("""
            SELECT o.orderID, o.date, o.totalPrice, c.cName,
                   SUM(CASE WHEN f.productID IS NULL THEN 0 ELSE 1 END) as confirmed_count,
                   COUNT(*) as total_products
            FROM Orders o
            JOIN Customer c ON o.userID = c.userID
            JOIN Contains co ON o.orderID = co.orderID
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON o.orderID = f.orderID AND co.productID = f.productID
            WHERE p.userID = %s
            GROUP BY o.orderID, o.date, o.totalPrice, c.cName
            HAVING confirmed_count < total_products OR confirmed_count = 0
        """, (user_id,))
        
        orders = cursor.fetchall()
        
        order_details = []
        for order in orders:
            # Get all products in this order from this supplier
            cursor.execute("""
                SELECT p.productID, p.pName, co.productQuantity, 
                       CASE WHEN f.productID IS NULL THEN FALSE ELSE TRUE END as confirmed
                FROM Contains co
                JOIN Product p ON co.productID = p.productID
                LEFT JOIN Fulfill f ON co.orderID = f.orderID AND co.productID = f.productID
                WHERE co.orderID = %s AND p.userID = %s
            """, (order['orderID'], user_id))
            
            products = cursor.fetchall()
            
            all_confirmed = all(p['confirmed'] for p in products)
            
            order_details.append({
                "orderID": order['orderID'],
                "date": order['date'],
                "totalPrice": order['totalPrice'],
                "cName": order['cName'],
                "products": products,
                "allConfirmed": all_confirmed
            })

        return jsonify(order_details)
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
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        data = request.json
        if not data.get('orderID') or not data.get('productID'):
            return jsonify({"error": "Missing orderID or productID"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify the product belongs to this supplier
        cursor.execute("""
            SELECT p.productID 
            FROM Product p
            WHERE p.productID = %s AND p.userID = %s
        """, (data['productID'], user_id))
        if not cursor.fetchone():
            return jsonify({"error": "Product does not belong to you"}), 403

        # 2. Find a warehouse with sufficient stock
        cursor.execute("""
            SELECT s.warehouseID, s.productQuantity
            FROM Storage s
            JOIN Supplies sp ON s.warehouseID = sp.warehouseID
            WHERE s.productID = %s AND sp.userID = %s
        """, (data['productID'], user_id))
        
        warehouses = cursor.fetchall()
        
        # Get the required quantity from the order
        cursor.execute("""
            SELECT productQuantity 
            FROM Contains 
            WHERE orderID = %s AND productID = %s
        """, (data['orderID'], data['productID']))
        
        required_quantity = cursor.fetchone()['productQuantity']
        
        # Find a warehouse with sufficient stock
        warehouse_id = None
        for warehouse in warehouses:
            if warehouse['productQuantity'] >= required_quantity:
                warehouse_id = warehouse['warehouseID']
                break
        
        if not warehouse_id:
            return jsonify({"error": "Insufficient stock in any warehouse"}), 400

        # 3. Update the Fulfill table
        cursor.execute("""
            INSERT INTO Fulfill (warehouseID, orderID, productID)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE warehouseID = VALUES(warehouseID)
        """, (warehouse_id, data['orderID'], data['productID']))

        # 4. Reduce the stock in the warehouse
        cursor.execute("""
            UPDATE Storage
            SET productQuantity = productQuantity - %s
            WHERE warehouseID = %s AND productID = %s
        """, (required_quantity, warehouse_id, data['productID']))

        conn.commit()
        return jsonify({"success": True, "message": "Product confirmed successfully"})
    except mysql.connector.Error as err:
        if conn: conn.rollback()
        return jsonify({"error": f"Database error: {err}"}), 500
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@supplier_bp.route('/assign_transport', methods=['POST'])
def assign_transport():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401

        data = request.json
        if not data.get('orderID'):
            return jsonify({"error": "Missing orderID"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify all products are confirmed
        cursor.execute("""
            SELECT co.productID, 
                   CASE WHEN f.productID IS NULL THEN 0 ELSE 1 END as confirmed
            FROM Contains co
            JOIN Product p ON co.productID = p.productID
            LEFT JOIN Fulfill f ON co.orderID = f.orderID AND co.productID = f.productID
            WHERE co.orderID = %s AND p.userID = %s
        """, (data['orderID'], user_id))
        
        products = cursor.fetchall()
        
        if not all(p['confirmed'] for p in products):
            return jsonify({"error": "Not all products are confirmed"}), 400

        # 2. Find an available transport
        cursor.execute("""
            SELECT transportID 
            FROM Transport 
            WHERE status = 'Available'
            ORDER BY RAND() 
            LIMIT 1
        """)
        
        transport = cursor.fetchone()
        
        if not transport:
            return jsonify({"error": "No available transports"}), 400

        # 3. Assign the transport to the order
        cursor.execute("""
            UPDATE Transport
            SET orderID = %s, status = 'Assigned'
            WHERE transportID = %s
        """, (data['orderID'], transport['transportID']))

        # 4. Update order status (assuming you have a status column in Orders)
        cursor.execute("""
            UPDATE Orders
            SET status = 'Processing'
            WHERE orderID = %s
        """, (data['orderID'],))

        conn.commit()
        return jsonify({
            "success": True,
            "message": "Transport assigned successfully",
            "transportID": transport['transportID']
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

@supplier_bp.route('/supplier_orders', methods=['GET'])
def get_supplier_orders():
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
                orders[item['orderID']] = {
                    'orderID': item['orderID'],
                    'orderDate': item['orderDate'],
                    'customerName': item['customerName'],
                    'products': [],
                    'allConfirmed': True
                }
            
            orders[item['orderID']]['products'].append({
                'id': item['productID'],
                'name': item['productName'],
                'quantity': item['quantity'],
                'confirmed': bool(item['confirmed'])
            })
            
            if not item['confirmed']:
                orders[item['orderID']]['allConfirmed'] = False
        
        return jsonify(list(orders.values()))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Use the same confirm_product and assign_transport endpoints from previous examples