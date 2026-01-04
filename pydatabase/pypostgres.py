import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import execute_batch, execute_values
from contextlib import contextmanager
from typing import List, Tuple, Optional, Dict, Any

from pyreusables.configs.credentials import credentials


#//===================== Postgres Connection =====================//
class PostgresConnectionPool:
    def __init__(self, db_name: str):
        creds = credentials.db_credentials(db_type='postgres', db_name=db_name)

        self._pool = ThreadedConnectionPool(
            minconn=credentials.DB_POOL_MIN,
            maxconn=credentials.DB_POOL_MAX,
            host=creds["host"],
            port=creds["port"],
            database=creds["database"],
            user=creds["user"],
            password=creds["password"],
        )

    @contextmanager
    def connection(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self):
        self._pool.closeall()



#//===================== Postgres CURD =====================//
class PyPostgres:
    def __init__(self, db_name: str):
        self.pool = PostgresConnectionPool(db_name)

    # ---------------- READ ----------------
    def fetch(self, sql: str, params: Optional[Tuple] = None):
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                
                return rows, cols

    # ---------------- WRITE ----------------
    def execute(self, sql: str, params: Optional[Tuple] = None) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.rowcount

    def executemany(self, sql: str, params_list: List[Tuple], batch: bool = True) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                if batch:
                    execute_batch(cur, sql, params_list)
                else:
                    cur.executemany(sql, params_list)
                return cur.rowcount

    # ---------------- BULK INSERT ----------------
    def insert_bulk(self, table: str, rows: List[Tuple], columns: List[str]):
        if not rows:
            return

        cols = f"({', '.join(columns)})"
        sql = f"INSERT INTO {table} {cols} VALUES %s"

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows)


    def insert_df(self, df, table: str) -> None:
        if df is None or df.empty:
            return

        self.insert_bulk(
            table=table,
            rows=[tuple(r) for r in df.to_numpy()],
            columns=df.columns.tolist()
        )

    # ---------------- BULK UPSERT ----------------
    def upsert_bulk(self, sql: str, rows: List[Tuple], page_size: int = 300) -> int:
        """
        Execute a bulk UPSERT using execute_values.
        SQL must contain VALUES %s.
        """
        if not rows:
            return 0

        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, sql, rows, page_size=page_size)
                return cur.rowcount
