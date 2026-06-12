#!/usr/bin/env python3
"""
Initialize MarginGuard Database

This script:
1. Creates the marginGuard database (if it doesn't exist)
2. Enables pgvector extension
3. Creates tables
4. Optionally seeds with sample products

Usage:
    python init_db.py
"""

import psycopg2
from psycopg2 import sql
import sys
import time
from datetime import datetime

# Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_USER = "postgres"
DB_PASSWORD = "varsh"
TARGET_DB = "marginguard"

# Sample products for seeding
SEED_PRODUCTS = [
    {
        "name": "AirPods Pro",
        "category": "wireless earbuds",
        "price": 249.00,
        "cost": 100.00,
        "margin_floor": 30,
        "features": "Active noise cancellation, transparency mode, spatial audio, adaptive audio, personalized volume",
        "competitor": "Apple",
    },
    {
        "name": "Sony WF-1000XM5",
        "category": "wireless earbuds",
        "price": 299.99,
        "cost": 120.00,
        "margin_floor": 32,
        "features": "Industry-leading noise cancellation, LDAC codec, 8-hour battery, multipoint connection",
        "competitor": "Sony",
    },
    {
        "name": "Samsung Galaxy Buds2 Pro",
        "category": "wireless earbuds",
        "price": 229.99,
        "cost": 92.00,
        "margin_floor": 35,
        "features": "Active noise cancellation, ambient sound, IPX7 water resistance, touch controls",
        "competitor": "Samsung",
    },
]


def log(msg, level="INFO"):
    """Print formatted log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level:8} {msg}")


def connect_postgres(db_name=None):
    """Connect to PostgreSQL"""
    config = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    if db_name:
        config["database"] = db_name

    try:
        conn = psycopg2.connect(**config)
        return conn
    except Exception as e:
        log(f"Connection failed: {e}", "ERROR")
        return None


def create_database():
    """Create marginGuard database"""
    try:
        # Connect to default postgres db
        conn = connect_postgres("postgres")
        if not conn:
            return False

        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{TARGET_DB}';"
        )
        exists = cursor.fetchone()

        if exists:
            log(f"Database '{TARGET_DB}' already exists", "SKIP")
        else:
            cursor.execute(f"CREATE DATABASE {TARGET_DB};")
            log(f"Created database '{TARGET_DB}'", "OK")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        if "already exists" in str(e).lower():
            log(f"Database '{TARGET_DB}' already exists", "SKIP")
            return True
        log(f"Error creating database: {e}", "ERROR")
        return False


def enable_pgvector():
    """Enable pgvector extension"""
    try:
        conn = connect_postgres(TARGET_DB)
        if not conn:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            log("Enabled pgvector extension", "OK")
        except psycopg2.Error as e:
            if "already exists" in str(e):
                log("pgvector extension already enabled", "SKIP")
                conn.rollback()
            else:
                raise

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        log(f"Error enabling pgvector: {e}", "ERROR")
        return False


def create_tables():
    """Create tables"""
    try:
        conn = connect_postgres(TARGET_DB)
        if not conn:
            return False

        cursor = conn.cursor()

        # Policies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id SERIAL PRIMARY KEY,
                section_title VARCHAR(255),
                content TEXT,
                embedding vector(384),
                filename VARCHAR(255),
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        log("Created 'policies' table", "OK")

        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                price DECIMAL(10, 2),
                cost DECIMAL(10, 2),
                margin_floor INTEGER,
                features TEXT,
                competitor VARCHAR(100),
                embedding vector(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        log("Created 'products' table", "OK")

        # Create indexes
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS policies_embedding_idx
                ON policies USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 10);
            """)
            log("Created policies vector index", "OK")
        except Exception:
            pass

        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS products_embedding_idx
                ON products USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            log("Created products vector index", "OK")
        except Exception:
            pass

        conn.commit()
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        log(f"Error creating tables: {e}", "ERROR")
        return False


def seed_products():
    """Seed sample products"""
    try:
        from sentence_transformers import SentenceTransformer

        log("Loading embedding model (first time takes ~30s)...", "INFO")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        log("Model loaded", "OK")

        conn = connect_postgres(TARGET_DB)
        if not conn:
            return False

        cursor = conn.cursor()

        # Check if products already exist
        cursor.execute("SELECT COUNT(*) FROM products;")
        count = cursor.fetchone()[0]

        if count > 0:
            log(f"Products table already has {count} records, skipping seed", "SKIP")
            cursor.close()
            conn.close()
            return True

        for product in SEED_PRODUCTS:
            # Generate embedding
            text_to_embed = f"{product['name']} {product['category']} {product['features']}"
            embedding = model.encode(text_to_embed).tolist()

            cursor.execute("""
                INSERT INTO products (name, category, price, cost, margin_floor, features, competitor, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product["name"],
                product["category"],
                product["price"],
                product["cost"],
                product["margin_floor"],
                product["features"],
                product["competitor"],
                embedding,
            ))

        conn.commit()
        log(f"Seeded {len(SEED_PRODUCTS)} sample products", "OK")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        log(f"Error seeding products: {e}", "ERROR")
        return False


def verify_connection():
    """Verify PostgreSQL is running"""
    try:
        conn = connect_postgres("postgres")
        if not conn:
            return False

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        log(f"Connected to: {version.split(',')[0]}", "OK")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        log(f"Verification failed: {e}", "ERROR")
        return False


def main():
    print("\n" + "=" * 60)
    print("  MarginGuard Database Initialization")
    print("=" * 60 + "\n")

    # Check PostgreSQL connection
    log("Checking PostgreSQL connection...", "INFO")
    if not verify_connection():
        print("\nERROR: PostgreSQL is not running or not accessible")
        print("   Please start PostgreSQL and try again")
        sys.exit(1)

    # Initialize database
    print("\nCreating database...")
    if not create_database():
        print("\nERROR: Failed to create database")
        sys.exit(1)

    # Wait for database to be available
    time.sleep(1)

    # Enable pgvector
    print("\nEnabling pgvector extension...")
    if not enable_pgvector():
        print("\nWARNING: Could not enable pgvector (may already be enabled)")

    # Create tables
    print("\nCreating tables...")
    if not create_tables():
        print("\nERROR: Failed to create tables")
        sys.exit(1)

    # Seed products
    print("\nSeeding sample data...")
    if not seed_products():
        print("\nWARNING: Failed to seed products (continuing anyway)")

    print("\n" + "=" * 60)
    print("SUCCESS: Database initialization complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Upload a policy in the frontend")
    print("3. Analyze a product - results use your real policies!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
