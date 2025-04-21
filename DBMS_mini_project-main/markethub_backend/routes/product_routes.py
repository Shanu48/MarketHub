from flask import Blueprint, jsonify
import mysql.connector

# Blueprint for product-related routes
product_blueprint = Blueprint("product", __name__)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="Aditi",
        password="Aditi@0830",
        database="MarketHub"
    )

# Route to fetch all products
@product_blueprint.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.productID, p.pName, p.description, p.price, p.unit, c.categoryName, s.sName
        FROM Product p
        JOIN Category c ON p.categoryName = c.categoryName
        JOIN Supplier s ON p.userID = s.userID;
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

# Route to get all categories
@product_blueprint.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT categoryName FROM Category")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(categories)

# Route to get all suppliers
@product_blueprint.route("/suppliers", methods=["GET"])
def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT sName FROM Supplier")
    suppliers = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(suppliers)
