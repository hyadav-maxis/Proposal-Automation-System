"""
One-time setup: create database, run schema, create .env and directories.
Uses default postgres connection (localhost, postgres user).
Set PGPASSWORD env var or use .env for DB_PASSWORD when running.
"""
import os
import sys

# Load .env if it exists (for DB_PASSWORD)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_NAME = os.getenv("DB_NAME", "proposal_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def main():
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "database_schema.sql")
    env_example = os.path.join(base_dir, ".env.example")
    env_path = os.path.join(base_dir, ".env")
    contracts_dir = os.path.join(base_dir, "contracts")

    # Connect to default 'postgres' database to create proposal_db
    conn_params = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
    }
    if DB_PASSWORD:
        conn_params["password"] = DB_PASSWORD
    try:
        conn = psycopg2.connect(database="postgres", **conn_params)
    except Exception as e:
        print("Could not connect to PostgreSQL:", e)
        print("Set DB_PASSWORD in .env or PGPASSWORD in environment if needed.")
        sys.exit(1)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create database if not exists
    cur.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    if cur.fetchone():
        print(f"Database '{DB_NAME}' already exists.")
    else:
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"Created database '{DB_NAME}'.")

    cur.close()
    conn.close()

    # Connect to proposal_db and run schema
    conn_params["database"] = DB_NAME
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    with open(schema_path, "r") as f:
        schema_sql = f.read()
    cur.execute(schema_sql)
    conn.commit()
    print("Schema applied successfully.")

    cur.close()
    conn.close()

    # Create contracts directory
    os.makedirs(contracts_dir, exist_ok=True)
    print("Created 'contracts' directory.")

    # Create .env from .env.example if .env does not exist
    if not os.path.exists(env_path) and os.path.exists(env_example):
        with open(env_example, "r") as f:
            env_content = f.read()
        with open(env_path, "w") as f:
            f.write(env_content)
        print("Created .env from .env.example. Edit .env to set DB_PASSWORD.")
    elif os.path.exists(env_path):
        print(".env already exists.")
    else:
        print("No .env.example found; .env not created.")

    print("\nSetup complete. Start the API with: python main.py")

if __name__ == "__main__":
    main()
