"""
Setup script for Proposal Automation System
Run this to initialize the database and create necessary directories
"""

import os
import psycopg2
from dotenv import load_dotenv

def setup_database():
    """Setup database connection and create tables"""
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'proposal_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Read and execute schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'database_schema.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Database schema created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. Database exists (CREATE DATABASE proposal_db;)")
        print("3. .env file is configured correctly")

def create_directories():
    """Create necessary directories"""
    directories = ['contracts']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}/")

if __name__ == "__main__":
    print("Setting up Proposal Automation System...")
    print("=" * 50)
    
    create_directories()
    print()
    
    response = input("Do you want to setup the database schema? (y/n): ")
    if response.lower() == 'y':
        setup_database()
    else:
        print("Skipping database setup. Run database_schema.sql manually.")
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Configure .env file with your database credentials")
    print("2. Run: python main.py")
    print("3. Open index.html in your browser")
