import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

def build_connection():
    load_dotenv()
    connection = psycopg2.connect(
        host="localhost",
        port=os.getenv("POSTGRE_PORT"),
        dbname="ecom_platform_db",
        user="postgres",
        password=os.getenv("POSTGRES_PASSWORD"),
        cursor_factory=RealDictCursor,
    )
    return connection

