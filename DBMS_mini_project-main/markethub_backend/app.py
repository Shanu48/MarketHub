from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import random
import os
from flask_cors import CORS
from routes.product_routes import product_blueprint
from routes.auth_routes import auth_bp
from routes.auth_routes import profile_bp
from routes.supplier_routes import supplier_bp
from routes.returns_routes import returns_blueprint
from routes.complaints_routes import complaints_bp
from datetime import datetime
from werkzeug.utils import secure_filename
from routes.warehouse_routes import warehouse_bp

from flask import send_from_directory


app = Flask(__name__)

app.secret_key = "Shanu@04082005"

# Enable CORS
# Apply CORS to all routes
# In app.py - REPLACE your current CORS setup with this:
# In app.py - Replace your current CORS setup with this:
CORS(app, supports_credentials=True)

@app.route('/orders/place', methods=['OPTIONS', 'POST'])
def place_order():
    if request.method == 'OPTIONS':
        # Pre-flight request
        response = jsonify()
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # Handle POST order submission
    try:
        data = request.get_json()
        payment_method = data.get("paymentMethod")
        items = data.get("items")
        total_amount = data.get("totalAmount")

        if not payment_method or not items or not total_amount:
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Simulate storing the order
        order_id = random.randint(1000, 9999)
        print(f" Order placed: ID {order_id}, Payment: {payment_method}, Items: {items}, Total: ₹{total_amount}")

        return jsonify({"success": True, "orderID": order_id})

    except Exception as e:
        print("Error placing order:", e)
        return jsonify({"success": False, "error": str(e)}), 500

    
# Add this after CORS setup for debugging
@app.after_request
def log_headers(response):
    """Debugging endpoint to log all response headers"""
    print("\nResponse Headers:")
    for name, value in response.headers.items():
        print(f"{name}: {value}")
    print()
    return response

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(product_blueprint, url_prefix='/')
app.register_blueprint(supplier_bp) 
app.register_blueprint(returns_blueprint, url_prefix='/api')
app.register_blueprint(warehouse_bp, url_prefix='/')
app.register_blueprint(complaints_bp, url_prefix='/api')


# Serve product page
@app.route('/products')
def products():
    return render_template("products.html")

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('pages', filename)

@app.route("/get_user_id")
def get_user_id():
    try:
        with open("logged_in_user.txt", "r") as file:
            user_id = file.read().strip()
            return jsonify({"userID": user_id})
    except FileNotFoundError:
        return jsonify({"error": "User not logged in"}), 400
    
@app.route('/supplier_dashboard')
def supplier_dashboard():
    return render_template("supplier_dashboard.html")


if __name__ == '__main__':
    app.run(debug=True)
