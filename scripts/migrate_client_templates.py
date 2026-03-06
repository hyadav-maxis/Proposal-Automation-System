import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "proposal_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgre")
DB_PORT = os.getenv("DB_PORT", "5432")

def migrate():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        print("Running migration: create_client_templates_table.sql...")
        
        sql_path = os.path.join(os.path.dirname(__file__), "..", "sql", "create_client_templates_table.sql")
        with open(sql_path, "r") as f:
            sql = f.read()
            
        cur.execute(sql)
        conn.commit()
        
        print("Migration completed successfully.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
