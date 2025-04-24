import os
from flask import Blueprint, jsonify, request
import mysql.connector
from datetime import datetime
import uuid
from pathlib import Path
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from db import get_db_connection
complaints_bp = Blueprint('complaints', __name__)

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
@complaints_bp.route('/supplier-complaints', methods=['GET'])
def get_supplier_complaints():
    conn = None
    cursor = None
    try:
        # Get logged in supplier ID
        supplier_id = get_logged_in_user()
        if not supplier_id:
            return jsonify({"success": False, "error": "Supplier not logged in"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get complaints for products this supplier provides
        cursor.execute("""
            SELECT r.returnID, r.orderID, r.reason, r.status, r.notes, 
                   r.supplier_response, r.response_date,
                   p.pName, p.productID, 
                   c.cName as customer_name,
                   o.date as order_date
            FROM Returns r
            JOIN Product p ON r.productID = p.productID
            JOIN Orders o ON r.orderID = o.orderID
            JOIN Customer c ON o.userID = c.userID
            WHERE p.userID = %s AND r.status = 'Pending'
            ORDER BY o.date DESC
        """, (supplier_id,))

        complaints = cursor.fetchall()
        
        # Format dates
        for complaint in complaints:
            complaint['order_date'] = complaint['order_date'].strftime('%Y-%m-%d') if complaint['order_date'] else None
            complaint['response_date'] = complaint['response_date'].strftime('%Y-%m-%d %H:%M') if complaint['response_date'] else None

        return jsonify({"success": True, "complaints": complaints})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@complaints_bp.route('/respond-complaint', methods=['POST'])
def respond_to_complaint():
    conn = None
    cursor = None
    try:
        supplier_id = get_logged_in_user()
        if not supplier_id:
            return jsonify({"success": False, "error": "Supplier not logged in"}), 401

        data = request.get_json()
        return_id = data.get('returnID')
        response = data.get('response')
        action = data.get('action')  # 'approve' or 'reject'

        if not all([return_id, response, action]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Update the return with supplier response
        cursor.execute("""
            UPDATE Returns 
            SET supplier_response = %s, 
                response_date = NOW(),
                supplier_id = %s,
                status = CASE WHEN %s = 'approve' THEN 'Approved' ELSE 'Rejected' END
            WHERE returnID = %s
        """, (response, supplier_id, action, return_id))

        conn.commit()
        return jsonify({"success": True, "message": "Response submitted successfully"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()