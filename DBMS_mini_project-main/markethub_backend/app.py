from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import random
import os
from flask_cors import CORS
from routes.product_routes import product_blueprint
from routes.auth_routes import auth_bp
from routes.auth_routes import profile_bp
from routes.cart_routes import cart_bp
from routes.supplier_routes import supplier_bp
from datetime import datetime
from werkzeug.utils import secure_filename

from flask import send_from_directory


app = Flask(__name__)

app.secret_key = "Shanu@04082005"

# Enable CORS
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(product_blueprint, url_prefix='/')
app.register_blueprint(cart_bp)
app.register_blueprint(supplier_bp) 


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
