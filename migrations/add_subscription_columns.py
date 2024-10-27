from sqlalchemy import create_engine, text
import os

def upgrade():
    # Get database URL from environment
    database_url = os.environ['DATABASE_URL']
    
    # Create engine
    engine = create_engine(database_url)
    
    # Execute migration in a transaction
    with engine.begin() as connection:
        # Add subscription columns to User table
        connection.execute(text("""
            ALTER TABLE "user" 
            ADD COLUMN IF NOT EXISTS subscription_type VARCHAR(20) DEFAULT 'free',
            ADD COLUMN IF NOT EXISTS subscription_end_date TIMESTAMP;
        """))
        
        # Create SubscriptionPlan table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS subscription_plan (
                id SERIAL PRIMARY KEY,
                name VARCHAR(20) UNIQUE NOT NULL,
                price FLOAT NOT NULL,
                duration_months INTEGER NOT NULL,
                features JSONB,
                stripe_price_id VARCHAR(100) UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Insert default subscription plans
            INSERT INTO subscription_plan (name, price, duration_months, features)
            VALUES 
                ('free', 0, 0, '{"features": ["Basic skill matching", "Limited video sessions", "Community access"]}'),
                ('basic', 9.99, 1, '{"features": ["Enhanced skill matching", "Unlimited video sessions", "Ad-free experience", "Priority support"]}'),
                ('premium', 19.99, 1, '{"features": ["All Basic features", "HD video", "Screen sharing", "Verified badges", "Expert sessions"]}')
            ON CONFLICT (name) DO NOTHING;
        """))

def downgrade():
    database_url = os.environ['DATABASE_URL']
    engine = create_engine(database_url)
    
    with engine.begin() as connection:
        # Drop subscription columns from User table
        connection.execute(text("""
            ALTER TABLE "user" 
            DROP COLUMN IF EXISTS subscription_type,
            DROP COLUMN IF EXISTS subscription_end_date;
        """))
        
        # Drop SubscriptionPlan table
        connection.execute(text('DROP TABLE IF EXISTS subscription_plan;'))

if __name__ == '__main__':
    upgrade()
    print("Migration completed successfully!")
