try:
    from db.connection import get_connection    # Normal case: project root is on PYTHONPATH and `db` is a package
except Exception:
    # Fallbacks for different ways the script may be executed:
    # - running from inside the `db` directory (python create_db.py)
    # - running the file directly without package context
    try:
        from connection import get_connection   # When current working directory is the `db` folder
    except Exception:
        import os   # As a last resort, add project parent directory to sys.path and import
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from db.connection import get_connection

def create_tables():
    """Create users table with embeddings column"""
    conn = get_connection()
    if not conn:
        print("Failed to connect to database")
        return
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")   # Enable pgvector extension
            # Create users table with embeddings as vector type (for concatenated embeddings)
            #I HAVE JUST IMPLEMENTED EXAPMLE HERE FOR CREATION OF TABLE FOR AN EMPLOYEES 
            #YOU CAN CHANGE THIS FOR YOUR REQUIREMENTS
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id VARCHAR(50) PRIMARY KEY,
                    username VARCHAR(100) NOT NULL,
                    department VARCHAR(100),
                    designation VARCHAR(100),
                    embeddings vector(2560)  -- For 5x512 concatenated embeddings
                );
            """)
            conn.commit()
            print("Tables created successfully")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()
        
if __name__ == "__main__":
    create_tables() # Allow running as a script: `python db/create_db.py` or `python -m db.create_db`
