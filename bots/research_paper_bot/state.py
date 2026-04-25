from typing import List
from utils.www.arxiv import ArvixResult
import psycopg

_DATABASE = "research_paper_bot"
_PG_URL = "postgresql://root:root@localhost:5432"

_SQL_CREATE_PAPERS_TABLE = """
CREATE TABLE IF NOT EXISTS arxiv_papers (
    id BIGSERIAL PRIMARY KEY,
    arxiv_entity_id VARCHAR(32),
    arxiv_id VARCHAR(32),
    arxiv_version INTEGER,
    url VARCHAR(128),
    title VARCHAR(512),
    summary TEXT,
    updated TIMESTAMP,
    published TIMESTAMP,
    UNIQUE(url)
)
"""
class StoreDriver:
    pass

class ArxivStore:
    def __init__(self):
        self._init_database()
        self.execute_ddl(_SQL_CREATE_PAPERS_TABLE)

        from psycopg_pool import ConnectionPool
        self._pool = ConnectionPool(
            f"{_PG_URL}/{_DATABASE}",
            max_size=10
        )
    

    def _init_database(self):
        conn = psycopg.connect(f"{_PG_URL}/postgres")
        conn.autocommit = True

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT 1 FROM pg_database WHERE datname = '{_DATABASE}';
            """)
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {_DATABASE};")

        conn.close()

    def _init_scheme(self):
        pass

    def insert_one(self, paper: ArvixResult):
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO arxiv_papers (
                        arxiv_entity_id,
                        arxiv_id,
                        arxiv_version,
                        url,
                        title,
                        summary,
                        updated,
                        published
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *;
                """, (
                    paper.arxiv_entity_id,
                    paper.arxiv_id,
                    paper.arxiv_version,
                    paper.url,
                    paper.title,
                    paper.summary,
                    paper.updated,
                    paper.published
                ))
                return cur.fetchone()
    
    def upsert_one(self, paper: ArvixResult):
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO arxiv_papers (
                        arxiv_entity_id,
                        arxiv_id,
                        arxiv_version,
                        url,
                        title,
                        summary,
                        updated,
                        published
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url)
                    DO UPDATE SET
                        arxiv_entity_id = EXCLUDED.arxiv_entity_id,
                        url = EXCLUDED.url,
                        title = EXCLUDED.title,
                        summary = EXCLUDED.summary,
                        updated = EXCLUDED.updated,
                        published = EXCLUDED.published
                    RETURNING *;
                """, (
                    paper.arxiv_entity_id,
                    paper.arxiv_id,
                    paper.arxiv_version,
                    paper.url,
                    paper.title,
                    paper.summary,
                    paper.updated,
                    paper.published
                ))
                return cur.fetchone()


    def execute_ddl(self, query: str):
        with psycopg.connect(f"{_PG_URL}/{_DATABASE}") as conn:
            with conn.cursor() as cur:
                cur.execute(query)

    def execute(self, query: str, params=None):
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if cur.description:  # SELECT
                    return cur.fetchall()
                return None

    def close(self):
        self._pool.close()
