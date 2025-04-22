# db.py
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "Aditi",
    "password": "Aditi@0830",
    "database": "MarketHub"
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)
