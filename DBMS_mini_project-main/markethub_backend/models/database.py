import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",      # Replace with your DB host
        user="Shanu48",           # Replace with your MySQL username
        password="Shanu@123", # Replace with your MySQL password
        database="MarketHub"   # Replace with your database name
    )
    return connection
