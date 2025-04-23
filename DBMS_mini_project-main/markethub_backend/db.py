# db.py
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "Shanu48",
    "password": "Shanu@123",
    "database": "MarketHub"
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
