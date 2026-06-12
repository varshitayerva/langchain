import psycopg2
from sentence_transformers import SentenceTransformer
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, EMBEDDING_MODEL
from seed_data import SEED_PRODUCTS, POLICY_DOC

def connect_db():
    """Connect to Postgres database"""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    return conn

def setup_extensions(conn):
    """Enable pgvector extension"""
    cursor = conn.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    conn.commit()
    cursor.close()
    print("✓ pgvector extension enabled")

def create_tables(conn):
    """Create products and policies tables with vector columns"""
    cursor = conn.cursor()

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

    # Policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id SERIAL PRIMARY KEY,
            section VARCHAR(255),
            content TEXT,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Create vector indexes for faster similarity search
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS products_embedding_idx
        ON products USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS policies_embedding_idx
        ON policies USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 10);
    """)

    conn.commit()
    cursor.close()
    print("✓ Tables created: products, policies")

def ingest_products(conn, model):
    """Ingest product data with embeddings"""
    cursor = conn.cursor()

    for product in SEED_PRODUCTS:
        # Create embedding from product name + features
        text_to_embed = f"{product['name']} {product['category']} {product['features']}"
        embedding = model.encode(text_to_embed).tolist()

        cursor.execute("""
            INSERT INTO products (name, category, price, cost, margin_floor, features, competitor, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            product['name'],
            product['category'],
            product['price'],
            product['cost'],
            product['margin_floor'],
            product['features'],
            product['competitor'],
            embedding
        ))

    conn.commit()
    cursor.close()
    print(f"✓ Ingested {len(SEED_PRODUCTS)} products with embeddings")

def ingest_policy(conn, model):
    """Ingest policy document with embeddings"""
    cursor = conn.cursor()

    # Split policy into sections
    sections = POLICY_DOC.split("## ")

    for i, section in enumerate(sections):
        if section.strip():
            # First section is just intro, skip "##"
            if i == 0:
                section_title = "Introduction"
                content = section
            else:
                lines = section.split("\n", 1)
                section_title = lines[0]
                content = lines[1] if len(lines) > 1 else ""

            embedding = model.encode(content).tolist()

            cursor.execute("""
                INSERT INTO policies (section, content, embedding)
                VALUES (%s, %s, %s);
            """, (section_title, content, embedding))

    conn.commit()
    cursor.close()
    print(f"✓ Ingested policy document with embeddings")

def main():
    print("\n🚀 Starting ingestion pipeline...\n")

    # Load embedding model
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to DB
    print("Connecting to Postgres...")
    conn = connect_db()

    # Setup
    setup_extensions(conn)
    create_tables(conn)

    # Ingest data
    ingest_products(conn, model)
    ingest_policy(conn, model)

    conn.close()
    print("\n✅ Ingestion complete!\n")

if __name__ == "__main__":
    main()
