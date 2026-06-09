import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

def create_database_if_not_exists():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"Database {DB_NAME} created successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not setup database directly from connection defaults: {e}")

def get_engine():
    conn_str = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(conn_str)

def initialize_schema():
    create_database_if_not_exists()
    
    engine = get_engine()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, 'sql', '01_schema_init.sql')
    views_path = os.path.join(base_dir, 'sql', '02_compliance_views.sql')

    with engine.connect() as conn:
        with open(schema_path, 'r') as f:
            conn.execute(text(f.read()))
        with open(views_path, 'r') as f:
            conn.execute(text(f.read()))
        conn.commit()
    print("Schema initialized.")
