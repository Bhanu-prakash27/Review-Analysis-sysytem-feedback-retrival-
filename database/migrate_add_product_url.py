# database/migrate_add_product_url.py
"""
Migration script to add product_url column to existing database
"""

from database.connection import get_database_connection

def migrate_database():
    """Add product_url column to raw_reviews table"""
    conn = get_database_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'review_analysis' 
            AND TABLE_NAME = 'raw_reviews' 
            AND COLUMN_NAME = 'product_url'
        """)
        
        result = cursor.fetchone()
        
        if result[0] == 0:
            print("Adding product_url column...")
            
            # Add column
            cursor.execute("""
                ALTER TABLE raw_reviews 
                ADD COLUMN product_url VARCHAR(500) AFTER product_name
            """)
            
            # Add index
            cursor.execute("""
                CREATE INDEX idx_product_url ON raw_reviews(product_url)
            """)
            
            conn.commit()
            print("Migration completed successfully!")
            print("Column 'product_url' added to 'raw_reviews' table")
            return True
        else:
            print("Column 'product_url' already exists. No migration needed.")
            return True
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()