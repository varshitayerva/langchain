import psycopg2
from sentence_transformers import SentenceTransformer
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, EMBEDDING_MODEL

class RAGAgent:
    def __init__(self):
        """Initialize RAG agent with embedding model and DB connection"""
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.db_config = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME,
        }

    def retrieve(self, query: str, top_k: int = 3):
        """
        Retrieve relevant products and policy snippets for a query.

        Args:
            query: Product search query (e.g., "wireless earbuds under $100")
            top_k: Number of results to return

        Returns:
            dict with product_data and policy_snippet
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Embed the query
            query_embedding = self.model.encode(query).tolist()

            # Search products by similarity
            cursor.execute(f"""
                SELECT id, name, category, price, cost, margin_floor, features, competitor,
                       1 - (embedding <=> %s::vector) as similarity
                FROM products
                ORDER BY embedding <=> %s::vector
                LIMIT {top_k};
            """, (query_embedding, query_embedding))

            products = cursor.fetchall()
            product_data = []
            for row in products:
                product_data.append({
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "price": float(row[3]),
                    "cost": float(row[4]),
                    "margin_floor": row[5],
                    "features": row[6],
                    "competitor": row[7],
                    "similarity": float(row[8])
                })

            # Search policies by similarity
            cursor.execute(f"""
                SELECT section, content,
                       1 - (embedding <=> %s::vector) as similarity
                FROM policies
                ORDER BY embedding <=> %s::vector
                LIMIT 2;
            """, (query_embedding, query_embedding))

            policies = cursor.fetchall()
            policy_snippet = "\n\n".join([f"### {p[0]}\n{p[1]}" for p in policies])

            cursor.close()
            conn.close()

            return {
                "query": query,
                "product_data": product_data,
                "policy_snippet": policy_snippet
            }

        except Exception as e:
            return {
                "error": f"RAG retrieval failed: {str(e)}",
                "query": query,
                "product_data": [],
                "policy_snippet": ""
            }

def rag_retrieve(query: str) -> dict:
    """
    Standalone RAG retrieval function.

    Args:
        query: Product search query

    Returns:
        dict with product_data and policy_snippet
    """
    rag = RAGAgent()
    return rag.retrieve(query)


# Test the RAG agent
if __name__ == "__main__":
    print("\n[TEST] RAG Agent Testing...\n")

    test_queries = [
        "wireless earbuds with noise cancellation",
        "affordable smartwatch under 300",
        "premium over-ear headphones",
    ]

    for query in test_queries:
        print(f"Query: {query}")
        result = rag_retrieve(query)

        if "error" in result:
            print(f"[ERROR] {result['error']}\n")
            continue

        print(f"\n[PRODUCTS] Top Results:")
        for p in result["product_data"]:
            print(f"  - {p['name']} (${p['price']}, similarity: {p['similarity']:.2f})")

        print(f"\n[POLICY] Relevant Rules:")
        print(f"  {result['policy_snippet'][:200]}...\n")
        print("-" * 80 + "\n")

    print("[SUCCESS] RAG Agent test complete!\n")
