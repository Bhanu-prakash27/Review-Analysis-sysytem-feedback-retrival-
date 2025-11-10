# clear_sample_data.py
from database.connection import get_database_connection

def clear_all_sample_data():
    """Remove all sample data from database"""
    conn = get_database_connection()
    if not conn:
        print("Database connection failed")
        return
    
    try:
        cursor = conn.cursor()
        
        # Delete in correct order (foreign key constraints)
        print("Deleting analysis results...")
        cursor.execute("DELETE FROM analysis_results")
        
        print("Deleting raw reviews...")
        cursor.execute("DELETE FROM raw_reviews")
        
        # Reset auto-increment
        cursor.execute("ALTER TABLE analysis_results AUTO_INCREMENT = 1")
        cursor.execute("ALTER TABLE raw_reviews AUTO_INCREMENT = 1")
        
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM raw_reviews")
        count = cursor.fetchone()[0]
        
        print(f"✅ Sample data cleared. Reviews remaining: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("⚠️  This will delete ALL reviews from the database!")
    confirm = input("Type 'YES' to continue: ")
    
    if confirm == "YES":
        clear_all_sample_data()
    else:
        print("Operation cancelled")