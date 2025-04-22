from flask import Blueprint, jsonify, request
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
        SELECT p.productID, p.pName, p.description, p.price, p.unit, c.categoryName, s.sName
        FROM Product p
        JOIN Category c ON p.categoryName = c.categoryName
        JOIN Supplier s ON p.userID = s.userID;
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

@product_blueprint.route("/cart/items", methods=["GET"])
def get_cart_items():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT c.productID, c.quantity, p.pName, p.description, p.price, p.unit
            FROM Cart c
            JOIN Product p ON c.productID = p.productID
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

@product_blueprint.route("/user/addresses", methods=["GET"])
def get_user_addresses():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Address WHERE userID = %s", (user_id,))
        addresses = cursor.fetchall()
        return jsonify({"success": True, "addresses": addresses})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": "Database error"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route('/orders/place', methods=['POST'])
def place_order():
    conn = None
    cursor = None
    try:
        print("DEBUG: Received request to place order")  # Debug log
        
        # 1. Get userID from logged_in_user.txt
        user_id = get_logged_in_user()
        if not user_id:
            print("DEBUG: User not logged in")  # Debug log
            return jsonify({"success": False, "error": "User not logged in"}), 401

        # Get request data
        data = request.get_json()
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        if not data:
            print("DEBUG: No data received in request")  # Debug log
            return jsonify({"success": False, "error": "No data received"}), 400

        address_details = data.get('addressDetails')
        payment_method = data.get('paymentMethod')
        items = data.get('items')
        total_amount = data.get('totalAmount')

        # Validate required data
        if not all([address_details, payment_method, items, total_amount]):
            print("DEBUG: Missing required fields in request")  # Debug log
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 2. Generate new orderID
        cursor.execute("SELECT orderID FROM Orders ORDER BY orderID DESC LIMIT 1")
        last_order = cursor.fetchone()
        if last_order:
            last_num = int(last_order[0][1:])
            new_order_id = f"O{last_num + 1:03d}"
        else:
            new_order_id = "O001"

        print(f"DEBUG: Generated order ID: {new_order_id}")  # Debug log

        # 3. Insert into Orders
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO Orders (orderID, date, totalPrice, userID) VALUES (%s, %s, %s, %s)",
            (new_order_id, today, total_amount, user_id)
        )
        print("DEBUG: Order record created")  # Debug log

        # 4. Handle address - first check if exists, then update or insert
        cursor.execute(
            "SELECT * FROM Address WHERE userID = %s", (user_id,)
        )
        existing_address = cursor.fetchone()
        
        if existing_address:
            # Update existing address
            cursor.execute(
                """UPDATE Address 
                SET houseNo = %s, streetName = %s, city = %s, state = %s, pin = %s
                WHERE userID = %s""",
                (address_details['houseNo'], address_details['streetName'],
                 address_details['city'], address_details['state'], 
                 address_details['pin'], user_id))
            print("DEBUG: Address record updated")
        else:
            # Insert new address
            cursor.execute(
                """INSERT INTO Address (userID, houseNo, streetName, city, state, pin)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, address_details['houseNo'], address_details['streetName'],
                 address_details['city'], address_details['state'], address_details['pin'])
            )
            print("DEBUG: Address record created")

        # 5. Insert order items
        for item in items:
            cursor.execute(
                "INSERT INTO Contains (orderID, productID, productQuantity) VALUES (%s, %s, %s)",
                (new_order_id, item['productID'], item['quantity'])
            )
        print(f"DEBUG: Added {len(items)} items to order")  # Debug log

        # 6. Clear cart
        cursor.execute("DELETE FROM Cart WHERE userID = %s", (user_id,))
        print("DEBUG: Cart cleared")  # Debug log
        
        conn.commit()
        print("DEBUG: Transaction committed successfully")  # Debug log
        return jsonify({
            'success': True,
            'message': 'Order placed successfully!',
            'orderID': new_order_id
        })

    except mysql.connector.Error as err:
        print(f"DEBUG: Database error: {err}")  # Debug log
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': 'Database error', 'details': str(err)}), 500
    except Exception as e:
        print(f"DEBUG: Unexpected error: {e}")  # Debug log
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()