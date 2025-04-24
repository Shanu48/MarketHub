import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",      # Replace with your DB host
        user="Aditi",           # Replace with your MySQL username
        password="Aditi@0830", # Replace with your MySQL password
        database="MarketHub"   # Replace with your database name
    )
    return connection
