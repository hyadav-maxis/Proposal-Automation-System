import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "proposal_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgre")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    # Check if column exists
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'proposal_details' AND column_name = 'resource_location'")
    exists = cur.fetchone()
    
    if not exists:
        print("Column 'resource_location' missing. Adding it...")
        cur.execute("ALTER TABLE proposal_details ADD COLUMN resource_location VARCHAR(50) DEFAULT 'standard';")
        conn.commit()
        print("Column added successfully.")
    else:
        print("Column 'resource_location' already exists.")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
