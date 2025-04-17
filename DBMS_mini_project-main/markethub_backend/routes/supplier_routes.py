from flask import Blueprint, request, jsonify
from models.database import get_db_connection

supplier_routes = Blueprint('supplier_routes', __name__)

@supplier_routes.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Supplier")
    suppliers = cursor.fetchall()
    connection.close()
    return jsonify(suppliers)

@supplier_routes.route('/api/suppliers', methods=['POST'])
def add_supplier():
    data = request.json
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO Supplier (userID, sName, email, phoneNo) VALUES (%s, %s, %s, %s)",
        (data['userID'], data['sName'], data['email'], data['phoneNo'])
    )
    connection.commit()
    connection.close()
    return jsonify({'message': 'Supplier added successfully!'})
