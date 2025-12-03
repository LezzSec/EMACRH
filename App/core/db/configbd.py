import mysql.connector




def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="emacViodos$13",
        database="emac_db",
        port=3306,
        charset="utf8mb4",
        use_unicode=True,
        autocommit=False
    )
    cur = conn.cursor()
    cur.execute("SET NAMES utf8mb4")
    cur.execute("SET CHARACTER SET utf8mb4")
    cur.close()
    return conn