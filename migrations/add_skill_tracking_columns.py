from sqlalchemy import create_engine, text
import os

def upgrade():
    # Get database URL from environment
    database_url = os.environ['DATABASE_URL']
    
    # Create engine
    engine = create_engine(database_url)
    
    # Execute migration in a transaction
    with engine.begin() as connection:
        # Add new columns
        connection.execute(text("""
            ALTER TABLE user_skill 
            ADD COLUMN IF NOT EXISTS total_hours FLOAT DEFAULT 0.0,
            ADD COLUMN IF NOT EXISTS last_session TIMESTAMP,
            ADD COLUMN IF NOT EXISTS sessions_completed INTEGER DEFAULT 0;
        """))
        
def downgrade():
    database_url = os.environ['DATABASE_URL']
    engine = create_engine(database_url)
    
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE user_skill 
            DROP COLUMN IF EXISTS total_hours,
            DROP COLUMN IF EXISTS last_session,
            DROP COLUMN IF EXISTS sessions_completed;
        """))

if __name__ == '__main__':
    upgrade()
    print("Migration completed successfully!")
