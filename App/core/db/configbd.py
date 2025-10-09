import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="emacViodos$13",
        database="emac_db"
    )
