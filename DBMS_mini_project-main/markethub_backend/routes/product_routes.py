from flask import Blueprint, jsonify
from flask import request, jsonify  # Add request here

import mysql.connector

# Blueprint for product-related routes
product_blueprint = Blueprint("product", __name__)

# Database connection function
# from:
# def get_db_connection():
#     return mysql.connector.connect(...

# to:
from db import get_db_connection


# Route to fetch all products
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

    # Print products to command prompt for debugging

    cursor.close()
    conn.close()

    return jsonify(products)

# Route to get all categories
@product_blueprint.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT categoryName FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(categories)

# Route to get all suppliers
@product_blueprint.route("/suppliers", methods=["GET"])
def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sName FROM Supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(suppliers)

from flask import request, jsonify  # Add missing request import

# Add these imports at the top
import os
from pathlib import Path

def get_logged_in_user():
    """Read userID from logged_in_user.txt in parent directory"""
    try:
        # Get path to parent directory of routes folder
        current_dir = Path(__file__).parent  # routes directory
        parent_dir = current_dir.parent      # markethub_backend directory
        file_path = parent_dir / "logged_in_user.txt"
        
        with open(file_path, "r") as f:
            user_id = f.read().strip()
            print(f"DEBUG: Read userID from file: {user_id}")  # For debugging
            return user_id
    except Exception as e:
        print(f"ERROR reading userID: {str(e)}")
        return None

# Modified cart route
@product_blueprint.route("/cart/add", methods=["POST"])
def add_to_cart():
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        
        print(f"DEBUG: Adding to cart - User: {user_id}, Product: {product_id}")  # Debugging

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify customer exists
        cursor.execute("SELECT * FROM Customer WHERE userID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "User not a customer"}), 400

        # Verify product exists
        cursor.execute("SELECT productID FROM Product WHERE productID = %s", (product_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "error": "Invalid product ID"}), 400

        # Insert/update cart
        cursor.execute("""
            INSERT INTO Cart (userID, productID, quantity)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (user_id, product_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Item added to cart"})

    except mysql.connector.Error as err:
        print(f"DB ERROR: {str(err)}")  # Debugging
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/cart/update", methods=["POST"])
def update_cart():
    try:
        print("\n[DEBUG] Received cart update request")
        user_id = get_logged_in_user()
        if not user_id:
            print("[ERROR] User not logged in")
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        quantity = data.get('quantity')
        
        print(f"[DEBUG] Updating cart - User: {user_id}, Product: {product_id}, New Qty: {quantity}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify product exists
        cursor.execute("SELECT productID FROM Product WHERE productID = %s", (product_id,))
        if not cursor.fetchone():
            print(f"[ERROR] Invalid product ID: {product_id}")
            return jsonify({"success": False, "error": "Invalid product ID"}), 400

        # Update cart quantity
        cursor.execute("""
            UPDATE Cart 
            SET quantity = %s
            WHERE userID = %s AND productID = %s
        """, (quantity, user_id, product_id))
        
        conn.commit()
        print("[SUCCESS] Cart updated successfully")
        return jsonify({"success": True, "message": "Cart updated"})

    except mysql.connector.Error as err:
        print(f"[DATABASE ERROR] {str(err)}")
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@product_blueprint.route("/cart/remove", methods=["POST"])
def remove_from_cart():
    try:
        print("\n[DEBUG] Received cart remove request")
        user_id = get_logged_in_user()
        if not user_id:
            print("[ERROR] User not logged in")
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        product_id = data.get('productID')
        
        print(f"[DEBUG] Removing from cart - User: {user_id}, Product: {product_id}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove item from cart
        cursor.execute("""
            DELETE FROM Cart 
            WHERE userID = %s AND productID = %s
        """, (user_id, product_id))
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        if affected_rows > 0:
            print("[SUCCESS] Item removed from cart")
            return jsonify({"success": True, "message": "Item removed from cart"})
        else:
            print("[ERROR] Item not found in cart")
            return jsonify({"success": False, "error": "Item not found in cart"}), 404

    except mysql.connector.Error as err:
        print(f"[DATABASE ERROR] {str(err)}")
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()