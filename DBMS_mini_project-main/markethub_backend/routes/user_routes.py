from flask import Blueprint, request, jsonify
from models.database import get_db_connection

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/api/users', methods=['GET'])
def get_users():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()
    connection.close()
    return jsonify(users)

@user_routes.route('/api/users', methods=['POST'])
def add_user():
    data = request.json
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO User (userID, password) VALUES (%s, %s)",
        (data['userID'], data['password'])
    )
    connection.commit()
    connection.close()
    return jsonify({'message': 'User added successfully!'})
