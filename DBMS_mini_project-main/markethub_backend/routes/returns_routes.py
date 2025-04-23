import os
from flask import Blueprint, jsonify, request
import mysql.connector
from datetime import datetime
import uuid
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

returns_blueprint = Blueprint("returns", __name__)

from db import get_db_connection

from flask import make_response

@returns_blueprint.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:5501')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def get_logged_in_user():
    try:
        current_dir = Path(__file__).parent
        file_path = current_dir.parent / "logged_in_user.txt"
        logger.debug(f"Looking for user file at: {file_path}")  # Add this
        if not file_path.exists():
            raise FileNotFoundError(f"User file not found at {file_path}")
            
        with open(file_path, "r") as f:
            user_id = f.read().strip()
            logger.debug(f"Found user ID: {user_id}")
            return user_id
    except Exception as e:
        logger.error(f"Error getting logged in user: {str(e)}")
        return None

@returns_blueprint.route("/order-options", methods=["GET"])
def get_order_options():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT o.orderID, o.date 
            FROM Orders o
            JOIN Contains c ON o.orderID = c.orderID
            WHERE o.userID = %s
            ORDER BY o.date DESC
            LIMIT 10
        """, (user_id,))

        orders = cursor.fetchall()
        return jsonify({"success": True, "orders": orders})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@returns_blueprint.route("/product-options/<order_id>", methods=["GET"])
def get_product_options(order_id):
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT p.productID, p.pName, p.unit, c.productQuantity
            FROM Contains c
            JOIN Product p ON c.productID = p.productID
            WHERE c.orderID = %s
        """, (order_id,))

        products = cursor.fetchall()
        return jsonify({"success": True, "products": products})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@returns_blueprint.route("/initiate", methods=["POST"])
def initiate_return():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        data = request.get_json()
        order_id = data.get('orderID')
        product_id = data.get('productID')
        reason = data.get('reason')
        notes = data.get('notes', '')

        if not all([order_id, product_id, reason]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Generate return ID
        return_id = f"RTN{uuid.uuid4().hex[:5].upper()}"

        cursor.execute("""
            INSERT INTO Returns (returnID, orderID, productID, reason, notes, status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """, (return_id, order_id, product_id, reason, notes))

        conn.commit()
        return jsonify({
            "success": True,
            "returnID": return_id,
            "message": "Return request submitted successfully"
        })

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@returns_blueprint.route("/history", methods=["GET"])
def get_return_history():
    conn = None
    cursor = None
    try:
        user_id = get_logged_in_user()
        if not user_id:
            return jsonify({"success": False, "error": "User not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT r.returnID, r.orderID, r.reason, r.status, r.notes,
                   p.pName, p.productID, o.date
            FROM Returns r
            JOIN Product p ON r.productID = p.productID
            JOIN Orders o ON r.orderID = o.orderID
            WHERE o.userID = %s
            ORDER BY o.date DESC
        """
        cursor.execute(query, (user_id,))

        returns = []
        for row in cursor.fetchall():
            returns.append({
                "returnID": row['returnID'],
                "orderID": row['orderID'],
                "product": f"{row['pName']} (ID: {row['productID']})",
                "reason": row['reason'],
                "status": row['status'],
                "notes": row['notes'],
                "date": row['date'].strftime('%Y-%m-%d')
            })

        return jsonify({"success": True, "returns": returns})

    except mysql.connector.Error as err:
        return jsonify({"success": False, "error": f"Database error: {err}"}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()