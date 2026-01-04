from mysql.connector import pooling
from typing import List, Tuple, Optional
from contextlib import contextmanager

from pyreusables.configs.credentials import credentials


#//===================== MySQL Connection =====================//
class MySQLConnectionPool:
    def __init__(self, db_name: str):
        creds = credentials.db_credentials(db_type='mysql', db_name=db_name)

        self._pool = pooling.MySQLConnectionPool(
            pool_name=f"{db_name}_pool",
            pool_size=credentials.DB_POOL_MAX,
            pool_reset_session=True,
            host=creds["host"],
            port=creds["port"],
            database=creds["database"],
            user=creds["user"],
            password=creds["password"],
        )

    @contextmanager
    def connection(self):
        conn = self._pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close(self):
        pass



#//===================== MySQL CURD =====================//
class PyMySQL:
    def __init__(self, db_name: str):
        self.pool = MySQLConnectionPool(db_name)

    # ---------- READ ----------
    def fetch(self, sql: str, params: Optional[Tuple] = None):
        with self.pool.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            cols = [c[0] for c in cur.description]
            cur.close()
            return rows, cols

    # ---------- WRITE ----------
    def execute(self, sql: str, params: Optional[Tuple] = None) -> int:
        with self.pool.connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            affected = cur.rowcount
            cur.close()
            return affected

    def executemany(self, sql: str, params_list: List[Tuple]) -> int:
        with self.pool.connection() as conn:
            cur = conn.cursor()
            cur.executemany(sql, params_list)
            affected = cur.rowcount
            cur.close()
            return affected

    # ---------- BULK INSERT ----------
    def insert_bulk(self, table: str, rows: List[Tuple], columns: List[str]) -> None:
        if not rows:
            return

        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        self.executemany(sql, rows)

    # ---------- BULK UPSERT ----------
    def upsert_bulk(self, sql: str, rows: List[Tuple]) -> int:
        if not rows:
            return 0
        self.executemany(sql, rows)
        return len(rows)

    def close(self):
        self.pool.close()
