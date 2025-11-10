import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import mysql.connector

# Load variables from .env file
load_dotenv()

def get_database_connection():
    """Return a mysql.connector connection"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Bhanu@2005"),
            database=os.getenv("DB_NAME", "review_analysis")
        )
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def get_sqlalchemy_engine():
    """Return SQLAlchemy engine"""
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "Bhanu@2005")
    host = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "review_analysis")

    connection_string = f"mysql+mysqlconnector://{user}:{password}@{host}/{db}"
    try:
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"❌ Error creating SQLAlchemy engine: {e}")
        return None
