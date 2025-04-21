from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error

cart_bp = Blueprint('cart', __name__)

# Database connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="Aditi",
        password="Aditi@0830",
            database="MarketHub"
        )
    except Error as e:
        print(f"Error: {e}")
        return None

@cart_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    user_id = data["userID"]
    product_id = data["productID"]
    quantity = data.get("quantity", 1)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()

    try:
        # Check if item already exists in cart
        cursor.execute(
            "SELECT quantity FROM cart WHERE userID = %s AND productID = %s",
            (user_id, product_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Update quantity
            cursor.execute(
                "UPDATE cart SET quantity = quantity + %s WHERE userID = %s AND productID = %s",
                (quantity, user_id, product_id)
            )
        else:
            # Insert new item
            cursor.execute(
                "INSERT INTO cart (userID, productID, quantity) VALUES (%s, %s, %s)",
                (user_id, product_id, quantity)
            )

        conn.commit()
        return jsonify({"message": "Item added to cart successfully"}), 200

    except Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@cart_bp.route('/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    user_id = data.get("userID")
    product_id = data.get("productID")
    quantity = data.get("quantity")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM cart WHERE userID = %s AND productID = %s",
            (user_id, product_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "UPDATE cart SET quantity = %s WHERE userID = %s AND productID = %s",
                (quantity, user_id, product_id)
            )
            conn.commit()
            return jsonify({"message": "Quantity updated"}), 200
        else:
            return jsonify({"message": "Item not found"}), 404

    except Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@cart_bp.route('/cart/remove', methods=['POST'])
def remove_cart():
    data = request.get_json()
    user_id = data.get("userID")
    product_id = data.get("productID")

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM cart WHERE userID = %s AND productID = %s",
            (user_id, product_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                "DELETE FROM cart WHERE userID = %s AND productID = %s",
                (user_id, product_id)
            )
            conn.commit()
            return jsonify({"message": "Removed from cart"}), 200
        else:
            return jsonify({"message": "Item not found"}), 404

    except Error as e:
        print(f"MySQL Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
