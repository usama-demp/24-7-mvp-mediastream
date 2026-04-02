import psycopg2

try:
    conn = psycopg2.connect(
        host="172.16.3.134",  # IP of host PC
        port=5432,
        database="stream_alt",
        user="postgres",
        password="admin123"
    )
    print("Connected successfully!")
except Exception as e:
    print("Connection failed:", e)