from sqlalchemy import create_engine, text
import os

def upgrade():
    # Get database URL from environment
    database_url = os.environ['DATABASE_URL']
    
    # Create engine
    engine = create_engine(database_url)
    
    # Execute migration in a transaction
    with engine.begin() as connection:
        # Add location column with default value
        connection.execute(text("""
            ALTER TABLE "user" 
            ADD COLUMN IF NOT EXISTS location VARCHAR(128) DEFAULT 'Not specified';
        """))
        
def downgrade():
    database_url = os.environ['DATABASE_URL']
    engine = create_engine(database_url)
    
    with engine.begin() as connection:
        connection.execute(text('ALTER TABLE "user" DROP COLUMN IF EXISTS location;'))

if __name__ == '__main__':
    upgrade()
    print("Migration completed successfully!")
