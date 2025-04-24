from flask import Blueprint, jsonify
import mysql.connector
import os
from db import get_db_connection

warehouse_bp = Blueprint('warehouse', __name__)

@warehouse_bp.route('/warehouses', methods=['GET'])
def get_warehouses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT w.warehouseID, w.location, w.capacity,
                   COUNT(DISTINCT s.userID) as supplier_count,
                   COUNT(DISTINCT st.productID) as product_count,
                   SUM(st.productQuantity) as total_items,
                   ROUND(SUM(st.productQuantity) / w.capacity * 100, 2) as capacity_percentage
            FROM Warehouse w
            LEFT JOIN Supplies s ON w.warehouseID = s.warehouseID
            LEFT JOIN Storage st ON w.warehouseID = st.warehouseID
            GROUP BY w.warehouseID, w.location, w.capacity
        """)
        warehouses = cursor.fetchall()

        # Updated image path handling (using absolute or correct relative path)
        for warehouse in warehouses:
            warehouse_id = warehouse['warehouseID']
            image_path = f"images/warehouses/{warehouse_id}.jpg"  # e.g., "W001.jpg"
            
            # Check if file exists (debugging step)
            full_path = os.path.join("pages", image_path)
            if not os.path.exists(full_path):
                image_path = f"images/warehouses/{warehouse_id}.png"
                full_path = os.path.join("pages", image_path)
                if not os.path.exists(full_path):
                    image_path = "images/warehouses/default.jpg"
            
            print(f"Debug: Warehouse {warehouse_id} -> Image Path: {image_path}")  # Debug log
            warehouse['image'] = image_path  # This will be used in the frontend

        return jsonify(warehouses)
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@warehouse_bp.route('/warehouse/<warehouse_id>', methods=['GET'])
def get_warehouse_details(warehouse_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get basic warehouse info
        cursor.execute("""
            SELECT w.*, 
                   COUNT(DISTINCT s.userID) as supplier_count,
                   COUNT(DISTINCT st.productID) as product_count,
                   SUM(st.productQuantity) as total_items
            FROM Warehouse w
            LEFT JOIN Supplies s ON w.warehouseID = s.warehouseID
            LEFT JOIN Storage st ON w.warehouseID = st.warehouseID
            WHERE w.warehouseID = %s
            GROUP BY w.warehouseID, w.location, w.capacity
        """, (warehouse_id,))
        
        warehouse = cursor.fetchone()
        if not warehouse:
            return jsonify({"error": "Warehouse not found"}), 404
        
        # Get image path
        image_path = f"images/warehouses/{warehouse_id}.jpg"
        if not os.path.exists(f"pages/{image_path}"):
            image_path = f"images/warehouses/{warehouse_id}.png"
            if not os.path.exists(f"pages/{image_path}"):
                image_path = "images/warehouses/default.jpg"
        warehouse['image'] = image_path
        
        # Get suppliers using this warehouse
        cursor.execute("""
            SELECT s.sName, s.email, s.phoneNo
            FROM Supplier s
            JOIN Supplies sp ON s.userID = sp.userID
            WHERE sp.warehouseID = %s
        """, (warehouse_id,))
        warehouse['suppliers'] = cursor.fetchall()
        
        # Get products stored in this warehouse
        cursor.execute("""
            SELECT p.productID, p.pName, p.price, p.unit, 
                   st.productQuantity as quantity,
                   cat.categoryName as category
            FROM Product p
            JOIN Storage st ON p.productID = st.productID
            LEFT JOIN Category cat ON p.categoryName = cat.categoryName
            WHERE st.warehouseID = %s
        """, (warehouse_id,))
        warehouse['products'] = cursor.fetchall()
        
        # Get capacity utilization
        warehouse['capacity_used'] = warehouse['total_items']
        warehouse['capacity_remaining'] = warehouse['capacity'] - warehouse['total_items']
        warehouse['capacity_percentage'] = round(warehouse['total_items'] / warehouse['capacity'] * 100, 2)
        
        return jsonify(warehouse)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()