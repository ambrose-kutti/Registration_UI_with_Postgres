import psycopg2

def get_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="face_registration",
            user="postgres",
            password="12345",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None