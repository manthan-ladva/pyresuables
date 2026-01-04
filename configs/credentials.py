from dotenv import load_dotenv
import os
import json


load_dotenv()

class Credentials:
    def db_credentials(self, db_type: str, db_name: str) -> dict:
        db_type = db_type.lower()
        db_name = db_name.upper()

        prefix = f"{db_type.upper()}_{db_name}"

        required_keys = {
            "host": f"{prefix}_HOST",
            "port": f"{prefix}_PORT",
            "database": f"{prefix}_DB",
            "user": f"{prefix}_USER",
            "password": f"{prefix}_PASSWORD",
        }

        creds = {}
        missing = []

        for key, env_var in required_keys.items():
            value = os.getenv(env_var)
            if value is None:
                missing.append(env_var)
            else:
                creds[key] = value

        if missing:
            raise RuntimeError(
                f"Missing environment variables for {db_type}/{db_name}: {missing}"
            )

        # Type normalization
        creds["port"] = int(creds["port"])

        return creds
        
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', '2'))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', '10'))


    #//---------------------------------// API Configurations
    LOCAL_API_HOST = os.getenv('LOCAL_API_HOST', 'http://127.0.0.1:8000')
        


credentials = Credentials()