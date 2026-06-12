"""
Database layer for MarginGuard API
Handles all Postgres operations for policies and products
"""

import psycopg2
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
from sentence_transformers import SentenceTransformer

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, EMBEDDING_MODEL


class Database:
    """Database manager for Postgres"""

    def __init__(self):
        self.db_config = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME,
        }
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.db_config)
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Enable pgvector
                try:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                except Exception:
                    pass  # Extension might already exist

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

                # Vector indexes
                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS policies_embedding_idx
                        ON policies USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 10);
                    """)
                except Exception:
                    pass

                try:
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS products_embedding_idx
                        ON products USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                except Exception:
                    pass

                conn.commit()
                cursor.close()
                return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    def store_policy(self, filename: str, sections: List[Dict[str, str]]) -> bool:
        """Store uploaded policy sections in database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                for section in sections:
                    title = section.get("title", "Untitled")
                    content = section.get("content", "")

                    # Generate embedding
                    embedding = self.embedding_model.encode(content).tolist()

                    cursor.execute("""
                        INSERT INTO policies (section_title, content, embedding, filename)
                        VALUES (%s, %s, %s, %s)
                    """, (title, content, embedding, filename))

                conn.commit()
                cursor.close()
                return True
        except Exception as e:
            print(f"Error storing policy: {e}")
            return False

    def search_policies(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Search policies by vector similarity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Embed query
                query_embedding = self.embedding_model.encode(query).tolist()

                # Search
                cursor.execute("""
                    SELECT section_title, content,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM policies
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (query_embedding, query_embedding, top_k))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "section": row[0],
                        "content": row[1],
                        "similarity": float(row[2])
                    })

                cursor.close()
                return results
        except Exception as e:
            print(f"Error searching policies: {e}")
            return []

    def search_products(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search products by vector similarity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Embed query
                query_embedding = self.embedding_model.encode(query).tolist()

                # Search
                cursor.execute("""
                    SELECT id, name, category, price, cost, margin_floor, features, competitor,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM products
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                """, (query_embedding, query_embedding, top_k))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "name": row[1],
                        "category": row[2],
                        "price": float(row[3]) if row[3] else None,
                        "cost": float(row[4]) if row[4] else None,
                        "margin_floor": row[5],
                        "features": row[6],
                        "competitor": row[7],
                        "similarity": float(row[8])
                    })

                cursor.close()
                return results
        except Exception as e:
            print(f"Error searching products: {e}")
            return []

    def get_all_policies(self) -> List[Dict[str, str]]:
        """Get all stored policies"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT section_title, content
                    FROM policies
                    ORDER BY upload_time DESC;
                """)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        "section": row[0],
                        "content": row[1]
                    })

                cursor.close()
                return results
        except Exception as e:
            print(f"Error getting policies: {e}")
            return []


# Global database instance
db = Database()
