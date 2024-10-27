from sqlalchemy import create_engine, text
import os

def verify_columns():
    try:
        # Get database URL from environment
        database_url = os.environ['DATABASE_URL']
        
        # Create engine
        engine = create_engine(database_url)
        
        # Execute verification query
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns
                WHERE table_name = 'user_skill'
                AND column_name IN ('total_hours', 'last_session', 'sessions_completed');
            """))
            
            columns = result.fetchall()
            
            if len(columns) == 3:
                print("All required columns exist:")
                for col in columns:
                    print(f"- {col[0]}: {col[1]}")
                return True
            else:
                existing = [col[0] for col in columns]
                missing = set(['total_hours', 'last_session', 'sessions_completed']) - set(existing)
                print(f"Missing columns: {missing}")
                return False
                
    except Exception as e:
        print(f"Error verifying columns: {str(e)}")
        return False

if __name__ == "__main__":
    verify_columns()
