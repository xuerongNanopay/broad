from psycopg_pool import ConnectionPool

_DATABASE = "research_paper_bot"

pool = ConnectionPool(
    f"postgresql://root:root@localhost:5432/{_DATABASE}",
    max_size=10
)


def _init_database():
    import psycopg
    conn = psycopg.connect("postgresql://root:root@localhost:5432/postgres")
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT 1 FROM pg_database WHERE datname = '{_DATABASE}';
        """)
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {_DATABASE};")

    conn.close()

def init_state():
    _init_database();
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            print(cur.fetchone())
    
    pool.close()