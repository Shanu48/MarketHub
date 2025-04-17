from flask import Blueprint, jsonify
import mysql.connector

# Blueprint for product-related routes
product_blueprint = Blueprint("product", __name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Shanu48",
        password="Shanu@123",
        database="MarketHub"
    )

# Route to fetch all products
@product_blueprint.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT p.productID, p.pName, p.description, p.price, p.unit, c.categoryName
    FROM Product p
    JOIN Category c ON p.categoryName = c.categoryName;
"""


    cursor.execute(query)
    products = cursor.fetchall()

    # Print products to command prompt for debugging
    print("\n--- Retrieved Products from Database ---")
    for product in products:
        print(product)
    print("----------------------------------------\n")

    cursor.close()
    conn.close()

    return jsonify(products)
