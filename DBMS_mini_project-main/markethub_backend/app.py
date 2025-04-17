from flask import Flask, render_template, request, redirect, url_for
import requests
import random
from flask_cors import CORS
from routes.product_routes import product_blueprint
from routes.auth_routes import auth_bp
from routes.auth_routes import profile_bp
from datetime import datetime

from flask import send_from_directory

app = Flask(__name__)

app.secret_key = "Shanu@04082005"

# Enable CORS
CORS(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(product_blueprint, url_prefix='/')

# Serve product page
@app.route('/products')
def products():
    return render_template("products.html")

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('pages', filename)

if __name__ == '__main__':
    app.run(debug=True)
