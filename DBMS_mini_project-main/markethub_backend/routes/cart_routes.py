from flask import Blueprint, request, jsonify
import mysql.connector
from mysql.connector import Error

cart_bp = Blueprint('cart', __name__)

# Database connection function
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="Shanu48",
            password="Shanu@123",
            database="MarketHub"
        )
    except Error as e:
        print(f"Error: {e}")
        return None


@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    productID = data.get("productID")
    userID = data.get("userID")
    quantity = data.get("quantity", 1)

    existing = Cart.query.filter_by(userID=userID, productID=productID).first()
    if existing:
        return jsonify({"message": "Product already in cart", "exists": True}), 200

    new_item = Cart(userID=userID, productID=productID, quantity=quantity)
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Added to cart", "exists": False}), 200

@cart_bp.route('/cart/update', methods=['POST'])
def update_cart():
    data = request.get_json()
    productID = data.get("productID")
    userID = data.get("userID")
    quantity = data.get("quantity")

    item = Cart.query.filter_by(userID=userID, productID=productID).first()
    if item:
        item.quantity = quantity
        db.session.commit()
        return jsonify({"message": "Quantity updated"}), 200
    else:
        return jsonify({"message": "Item not found"}), 404

@cart_bp.route('/cart/remove', methods=['POST'])
def remove_cart():
    data = request.get_json()
    productID = data.get("productID")
    userID = data.get("userID")

    item = Cart.query.filter_by(userID=userID, productID=productID).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Removed from cart"}), 200
    else:
        return jsonify({"message": "Item not found"}), 404
