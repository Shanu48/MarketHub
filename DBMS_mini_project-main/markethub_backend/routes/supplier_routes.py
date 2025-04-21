from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime

supplier_bp = Blueprint('supplier', __name__)

from db import get_db_connection

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

@supplier_bp.route('/get_warehouses', methods=['GET'])
def get_warehouses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get warehouses accessible to the supplier
        userID = 'SUP001'  # Replace with actual logged-in supplier ID
        cursor.execute("""
            SELECT w.warehouseID, w.location 
            FROM Warehouse w
            JOIN Supplies s ON w.warehouseID = s.warehouseID
            WHERE s.userID = %s
        """, (userID,))
        
        warehouses = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify(warehouses)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Add new product
# Add product and optionally to storage
@supplier_bp.route('/add_product', methods=['POST'])
def add_product():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.json
        userID = get_logged_in_user()

        pID = generate_new_product_id(cursor)
        cursor.execute("""
            INSERT INTO Product (productID, pName, description, price, unit, categoryName, userID, expiryDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (pID, data["pName"], data["description"], data["price"], data["unit"],
              data["categoryName"], userID, data["expiryDate"] or None))

        # Optional quantity + warehouse
        if data.get("warehouseID") and data.get("productQuantity"):
            cursor.execute("""
                INSERT INTO Storage (warehouseID, productID, productQuantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE productQuantity = productQuantity + VALUES(productQuantity)
            """, (data["warehouseID"], pID, data["productQuantity"]))

        conn.commit()
        return jsonify({"message": "Product added successfully", "productID": pID})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Get supplier products
@supplier_bp.route('/get_supplier_products')
def get_supplier_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        supplier_id = 'S001'  # Test with supplier S001

        query = """
        SELECT 
            p.productID,
            p.pName,
            p.price,
            p.unit,
            p.categoryName,
            p.expiryDate,
            GROUP_CONCAT(DISTINCT w.location SEPARATOR ', ') AS warehouseLocations,
            SUM(st.productQuantity) AS totalQuantity,
            MAX(CASE WHEN CURDATE() BETWEEN d.startDate AND d.endDate 
                THEN d.discountPercentage ELSE NULL END) AS discountPercentage
        FROM Product p
        LEFT JOIN Storage st ON p.productID = st.productID
        LEFT JOIN Warehouse w ON st.warehouseID = w.warehouseID
        LEFT JOIN Discount d ON p.productID = d.productID
        WHERE p.userID = %s
        GROUP BY p.productID
        """
        
        cursor.execute(query, (supplier_id,))
        products = cursor.fetchall()
                
        cursor.close()
        conn.close()
        
        return jsonify(products)
        
    except Exception as e:
        print("Database error:", str(e))
        return jsonify({"error": str(e)}), 500
    
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
