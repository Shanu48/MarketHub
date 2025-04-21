from flask import Blueprint, jsonify, request, redirect, render_template
import mysql.connector

auth_bp = Blueprint('auth', __name__)

profile_bp = Blueprint('profile', __name__)

from db import get_db_connection

# Utility to generate new userID
def generate_user_id(user_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if user_type == 'Customer':
        cursor.execute("SELECT COUNT(*) FROM Customer")
        count = cursor.fetchone()[0] + 1
        user_id = f"C{count}"
    else:
        cursor.execute("SELECT COUNT(*) FROM Supplier")
        count = cursor.fetchone()[0] + 1
        user_id = f"S{count}"

    cursor.close()
    conn.close()
    return user_id

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    role = data.get('role')  # "Supplier" or "Customer"
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Generate new user ID
    if role == "Customer":
        cursor.execute("SELECT COUNT(*) FROM Customer")
        count = cursor.fetchone()[0] + 1
        user_id = f"C{count:03d}"
    else:
        cursor.execute("SELECT COUNT(*) FROM Supplier")
        count = cursor.fetchone()[0] + 1
        user_id = f"S{count:03d}"

    # Insert into User table
    cursor.execute("INSERT INTO User (userID, password) VALUES (%s, %s)", (user_id, password))

    # Insert into Customer or Supplier table
    if role == "Customer":
        cursor.execute("INSERT INTO Customer (userID, cName, email, phoneNo) VALUES (%s, %s, %s, %s)",
                       (user_id, name, email, phone))
    else:
        cursor.execute("INSERT INTO Supplier (userID, sName, email, phoneNo) VALUES (%s, %s, %s, %s)",
                       (user_id, name, email, phone))

    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "success", "userID": user_id}



@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check Supplier table
    cursor.execute("""
        SELECT User.userID FROM Supplier
        JOIN User ON Supplier.userID = User.userID
        WHERE Supplier.email = %s AND User.password = %s
    """, (email, password))
    supplier_result = cursor.fetchone()

    if supplier_result:
        user_id = supplier_result[0]
        role = 'S'
    else:
        # Check Customer table
        cursor.execute("""
            SELECT User.userID FROM Customer
            JOIN User ON Customer.userID = User.userID
            WHERE Customer.email = %s AND User.password = %s
        """, (email, password))
        customer_result = cursor.fetchone()

        if customer_result:
            user_id = customer_result[0]
            role = 'C'
        else:
            cursor.close()
            conn.close()
            return {"status": "fail", "message": "Invalid credentials"}

    # Save user ID to file
    with open('logged_in_user.txt', 'w') as f:
        f.write(user_id)

    cursor.close()
    conn.close()

    return {"status": "success", "role": role}



@profile_bp.route('/profile', methods=['GET'])
def get_profile():
    try:
        # Step 1: Read the logged-in user ID
        with open("logged_in_user.txt", "r") as file:
            user_id = file.read().strip()

        # Step 2: Connect to database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Step 3: Determine role
        role = "Supplier" if user_id.startswith("S") else "Customer"

        # Step 4: Fetch basic info
        if role == "Supplier":
            cursor.execute("SELECT sName AS name, email, phoneNo AS phone FROM Supplier WHERE userID = %s", (user_id,))
        else:
            cursor.execute("SELECT cName AS name, email, phoneNo AS phone FROM Customer WHERE userID = %s", (user_id,))
        user_data = cursor.fetchone()

        # Step 5: Fetch address
        cursor.execute("""
            SELECT CONCAT(houseNo, ', ', streetName, ', ', city, ', ', state, ' - ', pin) AS address
            FROM Address WHERE userID = %s
        """, (user_id,))
        address_data = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user_data:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "role": role,
            "userID": user_id,
            "name": user_data["name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "address": address_data["address"] if address_data else "Not available"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
