# core/db/configbd.py
import os
import mysql.connector

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "emacViodos$13")
DB_NAME = os.getenv("DB_NAME", "emac_db")  

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME,
        autocommit=False,
    )

