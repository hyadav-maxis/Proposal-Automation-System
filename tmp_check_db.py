import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'proposal_details'")
    columns = [row[0] for row in cur.fetchall()]
    print(f"Columns: {columns}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
