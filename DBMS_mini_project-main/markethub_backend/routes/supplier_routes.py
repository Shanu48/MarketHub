from flask import Blueprint, request, jsonify
import mysql.connector
import os

supplier_bp = Blueprint('supplier', __name__)

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Shanu48",
        password="Shanu@123",
        database="MarketHub"
    )

# Read current logged-in user
def get_logged_in_user():
    try:
        with open("logged_in_user.txt", "r") as file:
            return file.read().strip()
    except:
        return None

# Generate unique product ID
def generate_new_product_id(cursor):
    cursor.execute("SELECT productID FROM Product ORDER BY productID DESC LIMIT 1")
    result = cursor.fetchone()
    if result:
        last_id = int(result[0][1:])
        new_id = f"P{last_id + 1:03}"
    else:
        new_id = "P001"
    return new_id

# Add new product
@supplier_bp.route('/add_product', methods=['POST'])
def add_product():
    conn = None
    cursor = None
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        pName = data.get("pName")
        description = data.get("description")
        price = data.get("price")
        unit = data.get("unit")
        categoryName = data.get("categoryName")
        expiryDate = data.get("expiryDate")

        if not all([pName, description, price, unit, categoryName]):
            return jsonify({"error": "Missing required fields"}), 400

        userID = get_logged_in_user()
        if not userID:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        productID = generate_new_product_id(cursor)

        insert_query = """
            INSERT INTO Product (productID, pName, description, price, unit, categoryName, userID, expiryDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (productID, pName, description, price, unit, categoryName, userID, expiryDate))

        storage_query = """
            INSERT INTO Storage (warehouseID, productID, productQuantity)
            VALUES (%s, %s, %s)
        """
        cursor.execute(storage_query, ('W001', productID, 0))

        conn.commit()

        cursor.execute("SELECT * FROM Product WHERE userID = %s", (userID,))
        products = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result = [dict(zip(columns, row)) for row in products]

        return jsonify({
            "message": "Product added successfully!",
            "productID": productID,
            "products": result
        }), 201

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Database error: {str(db_error)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# View all products by this supplier
@supplier_bp.route('/my_products', methods=['GET'])
def my_products():
    try:
        supplierID = get_logged_in_user()
        if not supplierID:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Product WHERE userID = %s", (supplierID,))
        products = cursor.fetchall()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Supplier stats (e.g., total products)
@supplier_bp.route('/supplier_stats', methods=['GET'])
def supplier_stats():
    try:
        supplierID = get_logged_in_user()
        if not supplierID:
            return jsonify({"error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Product WHERE userID = %s", (supplierID,))
        total_products = cursor.fetchone()[0]
        return jsonify({
            "total_products": total_products,
            "status": "Fetched successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# Get list of categories (optional use in dropdowns)
@supplier_bp.route("/get_categories", methods=["GET"])
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
