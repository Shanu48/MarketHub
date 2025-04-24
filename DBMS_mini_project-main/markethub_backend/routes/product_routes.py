from flask import Blueprint, jsonify, request, render_template  # Add render_template here
import mysql.connector
import os
from pathlib import Path
from datetime import datetime
import uuid
from db import get_db_connection

product_blueprint = Blueprint("product", __name__)

def get_logged_in_user():
    try:
        current_dir = Path(__file__).parent
        parent_dir = current_dir.parent
        file_path = parent_dir / "logged_in_user.txt"
        with open(file_path, "r") as f:
            user_id = f.read().strip()
            print(f"DEBUG: Read userID from file: {user_id}")
            return user_id
    except Exception as e:
        print(f"ERROR reading userID: {str(e)}")
        return None

@product_blueprint.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            p.productID, 
            p.pName, 
            p.description, 
            p.price as originalPrice,
            CASE 
                WHEN d.discountPercentage IS NOT NULL AND CURDATE() BETWEEN d.startDate AND d.endDate 
                THEN ROUND(p.price * (1 - d.discountPercentage/100))
                ELSE p.price
            END as sellingPrice,
            p.unit, 
            c.categoryName, 
            s.sName,
            d.discountPercentage
        FROM Product p
        JOIN Category c ON p.categoryName = c.categoryName
        JOIN Supplier s ON p.userID = s.userID
        LEFT JOIN Discount d ON p.productID = d.productID
            AND CURDATE() BETWEEN d.startDate AND d.endDate
        """
    cursor.execute(query)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(products)

@product_blueprint.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT categoryName FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(categories)

@product_blueprint.route("/suppliers", methods=["GET"])
def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sName FROM Supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(suppliers)

@product_blueprint.route("/cart/add", methods=["POST"])
def add_to_cart():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Customer WHERE userID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "User not a customer"}), 400

        cursor.execute("SELECT productID FROM Product WHERE productID = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Invalid product ID"}), 400

        cursor.execute("""
            INSERT INTO Cart (userID, productID, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (user_id, product_id))
        conn.commit()
        return jsonify({"success": True, "message": "Item added to cart"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/cart/update", methods=["POST"])
def update_cart():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        quantity = data.get('quantity')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT productID FROM Product WHERE productID = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Invalid product ID"}), 400

        cursor.execute("""
            UPDATE Cart 
            SET quantity = %s
            WHERE userID = %s AND productID = %s
        """, (quantity, user_id, product_id))
        conn.commit()
        return jsonify({"success": True, "message": "Cart updated"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/cart/clear", methods=["POST"])
def clear_cart():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM Cart 
            WHERE userID = %s
        """, (user_id,))
        affected_rows = cursor.rowcount
        conn.commit()

        if affected_rows > 0:
            return jsonify({"success": True, "message": "Cart cleared successfully"})
        else:
            return jsonify({"success": True, "message": "Cart was already empty"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM Cart 
            WHERE userID = %s AND productID = %s
        """, (user_id, product_id))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        if affected_rows > 0:
            return jsonify({"success": True, "message": "Item removed from cart"})
        else:
            return jsonify({"success": False, "error": "Item not found in cart"})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
@product_blueprint.route("/cart/items", methods=["GET"])
def get_cart_items():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.productID, c.quantity, p.pName, p.description, 
                CASE 
                    WHEN d.discountPercentage IS NOT NULL AND CURDATE() BETWEEN d.startDate AND d.endDate 
                    THEN ROUND(p.price * (1 - d.discountPercentage/100))
                    ELSE p.price
                END as price,
                p.unit
            FROM Cart c
            JOIN Product p ON c.productID = p.productID
            LEFT JOIN Discount d ON p.productID = d.productID
                AND CURDATE() BETWEEN d.startDate AND d.endDate
            WHERE c.userID = %s
        """, (user_id,))

        items = cursor.fetchall()
        return jsonify({"success": True, "items": items})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/user/address", methods=["GET"])
def get_user_address():
    conn = None
    cursor = None
    try:
        print("\n===== DEBUG: Starting address retrieval =====")
        
        # 1. Get logged in user
        user_id = get_logged_in_user()
        print(f"DEBUG: Retrieved user ID: {user_id}")
        if not user_id:
            print("DEBUG: No user ID found - not logged in")
            return jsonify({"success": False, "error": "User not logged in"}), 401

        # 2. Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        print("DEBUG: Database connection established")

        # 3. Execute query
        query = "SELECT houseNo, streetName, city, state, pin FROM Address WHERE userID = %s LIMIT 1"
        print(f"DEBUG: Executing query: {query} with userID: {user_id}")
        cursor.execute(query, (user_id,))
        
        # 4. Process results
        address = cursor.fetchone()
        print(f"DEBUG: Query result: {address}")
        
        if not address:
            print("DEBUG: No address found for user")
            return jsonify({"success": True, "address": None})
            
        print("DEBUG: Address found, returning response")
        response = jsonify({
            "success": True,
            "address": address
        })
        
        # 5. Debug CORS headers
        response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5501')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        print(f"DEBUG: Response headers: {response.headers}")
        
        return response

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
        print("===== DEBUG: Address retrieval completed =====\n")

@product_blueprint.route('/orders/place', methods=['POST'])
def place_order():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        payment_method = data.get('paymentMethod')
        items = data.get('items')
        total_amount = data.get('totalAmount')

        if not all([payment_method, items, total_amount]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate new orderID
        cursor.execute("SELECT orderID FROM Orders ORDER BY orderID DESC LIMIT 1")
        last_order = cursor.fetchone()
        if last_order:
            last_num = int(last_order[0][1:])
            new_order_id = f"O{last_num + 1:03d}"
        else:
            new_order_id = "O001"

        # Insert into Orders
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO Orders (orderID, date, totalPrice, userID) VALUES (%s, %s, %s, %s)",
            (new_order_id, today, total_amount, user_id)
        )

        # Handle address
        cursor.execute("SELECT * FROM Address WHERE userID = %s", (user_id,))
        existing_address = cursor.fetchone()
        
        # Insert order items with their final selling prices
        for item in items:
            cursor.execute(
                "INSERT INTO Contains (orderID, productID, productQuantity) VALUES (%s, %s, %s)",
                (new_order_id, item['productID'], item['quantity'])
            )

        # Clear cart
        cursor.execute("DELETE FROM Cart WHERE userID = %s", (user_id,))
        
        conn.commit()
        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'orderID': new_order_id
        })

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': 'Database error', 'details': str(err)}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/orders/history", methods=["GET", "OPTIONS"])
def get_order_history():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get order history with address details
        cursor.execute("""
            SELECT o.orderID, o.date, o.totalPrice, 
                   a.houseNo, a.streetName, a.city, a.state, a.pin
            FROM Orders o
            LEFT JOIN Address a ON o.userID = a.userID
            WHERE o.userID = %s
            ORDER BY o.orderID DESC
        """, (user_id,))
        orders = cursor.fetchall()

        # Get order items for each order with current discounted prices
        for order in orders:
            cursor.execute("""
                SELECT 
                    c.productID, 
                    c.productQuantity, 
                    p.pName, 
                    p.unit,
                    CASE 
                        WHEN d.discountPercentage IS NOT NULL AND CURDATE() BETWEEN d.startDate AND d.endDate 
                        THEN ROUND(p.price * (1 - d.discountPercentage/100))
                        ELSE p.price
                    END as price
                FROM Contains c
                JOIN Product p ON c.productID = p.productID
                LEFT JOIN Discount d ON p.productID = d.productID
                    AND CURDATE() BETWEEN d.startDate AND d.endDate
                WHERE c.orderID = %s
            """, (order['orderID'],))
            order['items'] = cursor.fetchall()

        return jsonify({"success": True, "orders": orders})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/order/track/<order_id>", methods=["GET", "OPTIONS"])
def track_order(order_id):
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify order belongs to user
        cursor.execute("""
            SELECT orderID FROM Orders 
            WHERE orderID = %s AND userID = %s
        """, (order_id, user_id))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Order not found"}), 404

        # Get order status
        cursor.execute("""
            SELECT t.status as transport_status, 
                   r.status as return_status,
                   o.date as order_date
            FROM Orders o
            LEFT JOIN Transport t ON o.orderID = t.orderID
            LEFT JOIN Returns r ON o.orderID = r.orderID
            WHERE o.orderID = %s
        """, (order_id,))
        status = cursor.fetchone()

        if not status:
            return jsonify({"success": False, "error": "Status not available"}), 404

        return jsonify({
            "success": True,
            "order_id": order_id,
            "status": {
                "order_date": status['order_date'].strftime('%Y-%m-%d') if status['order_date'] else None,
                "shipping": status['transport_status'] or "Preparing",
                "returns": status['return_status'] or "None"
            }
        })

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/orders-page")  # Route to serve the HTML page
def orders_page():
    return render_template("orders.html")