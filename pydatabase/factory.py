from pyreusables.pydatabase.pypostgres import PyPostgres
from pyreusables.pydatabase.py_mysql import PyMySQL



def database_factory(db_type: str, db_name: str):
    if db_type == "postgres":
        return PyPostgres(db_name)
    if db_type == "mysql":
        return PyMySQL(db_name)
    raise ValueError(f"Unsupported db_type: {db_type}")
