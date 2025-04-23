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