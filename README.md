# pyresuables

A collection of reusable Python components for building robust applications, including database connections, MQTT messaging, logging utilities, and configuration management.

## Features

- **Database Layer**: Connection-pooled database operations for PostgreSQL and MySQL
- **MQTT Messaging**: High-performance MQTT subscriber with worker pool for message processing
- **Logging**: Structured JSON logging with context variables
- **Configuration**: Environment-based credential management

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pyresuables
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (see Configuration section below).

## Configuration

Create a `.env` file in your project root with the following variables:

### Database Credentials
For PostgreSQL:
```
POSTGRES_<DB_NAME>_HOST=your_host
POSTGRES_<DB_NAME>_PORT=5432
POSTGRES_<DB_NAME>_DB=your_database
POSTGRES_<DB_NAME>_USER=your_user
POSTGRES_<DB_NAME>_PASSWORD=your_password
```

For MySQL:
```
MYSQL_<DB_NAME>_HOST=your_host
MYSQL_<DB_NAME>_PORT=3306
MYSQL_<DB_NAME>_DB=your_database
MYSQL_<DB_NAME>_USER=your_user
MYSQL_<DB_NAME>_PASSWORD=your_password
```

### Connection Pool Settings
```
DB_POOL_MIN=2
DB_POOL_MAX=10
```

### API Configuration
```
LOCAL_API_HOST=http://127.0.0.1:8000
```

## Usage

### Database Operations

#### Using the Database Factory
```python
from pyresuables.pydatabase.factory import database_factory

# Create a PostgreSQL connection
db = database_factory("postgres", "MYDB")

# Create a MySQL connection
db = database_factory("mysql", "MYDB")
```

#### PostgreSQL Operations
```python
from pyresuables.pydatabase.pypostgres import PyPostgres

db = PyPostgres("MYDB")

# Fetch data
rows, columns = db.fetch("SELECT * FROM users WHERE id = %s", (user_id,))

# Execute a query
affected_rows = db.execute("UPDATE users SET name = %s WHERE id = %s", ("John", user_id))

# Bulk insert
data = [("John", "john@example.com"), ("Jane", "jane@example.com")]
db.insert_bulk("users", data, ["name", "email"])

# Insert from DataFrame
import pandas as pd
df = pd.DataFrame({"name": ["John"], "email": ["john@example.com"]})
db.insert_df(df, "users")

# Bulk upsert
upsert_sql = "INSERT INTO users (id, name) VALUES %s ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name"
data = [(1, "John"), (2, "Jane")]
db.upsert_bulk(upsert_sql, data)
```

#### MySQL Operations
```python
from pyresuables.pydatabase.py_mysql import PyMySQL

db = PyMySQL("MYDB")

# Similar API to PostgreSQL
rows, columns = db.fetch("SELECT * FROM users WHERE id = %s", (user_id,))
affected_rows = db.execute("UPDATE users SET name = %s WHERE id = %s", ("John", user_id))
```

### MQTT Messaging

```python
from pyresuables.pymqtt.pymqtt import MQTTSubscriber

def message_handler(data, topic):
    print(f"Received on {topic}: {data}")
    # Process your message here

config = {
    "broker": "mqtt.example.com",
    "port": 1883,
    "username": "your_username",
    "password": "your_password"
}

subscriber = MQTTSubscriber(
    config=config,
    topic="sensors/temperature",
    callback=message_handler,
    workers=16,  # Number of worker threads
    max_queue=10000  # Max queue size for backpressure
)

subscriber.start()

# Later, to stop:
subscriber.stop()
```

### Logging

```python
from pyresuables.utilities.pylogger import log, info, error, debug, warning, exception
from pyresuables.utilities.pylogger import request_id, job_id, task_id, pipeline

# Set context variables
request_id.set("req-123")
job_id.set("job-456")

# Log messages
log.info("Application started")
info("Processing user data", user_id=123, action="login")
error("Database connection failed", error_code=500)
debug("Debug information", variable=value)

# Exception logging
try:
    risky_operation()
except Exception as e:
    exception("Operation failed", operation="risky_operation")
```

### Credentials Management

```python
from pyresuables.configs.credentials import credentials

# Get database credentials
creds = credentials.db_credentials("postgres", "MYDB")
print(creds)  # {'host': '...', 'port': 5432, 'database': '...', 'user': '...', 'password': '...'}

# Access other config
print(credentials.DB_POOL_MIN)  # 2
print(credentials.LOCAL_API_HOST)  # http://127.0.0.1:8000
```

## Project Structure

```
pyresuables/
├── configs/
│   ├── credentials.py          # Environment-based configuration
│   └── __init__.py
├── pydatabase/
│   ├── factory.py              # Database factory for creating connections
│   ├── pypostgres.py           # PostgreSQL operations
│   ├── py_mysql.py             # MySQL operations
│   └── __init__.py
├── pymqtt/
│   ├── pymqtt.py               # MQTT subscriber with worker pool
│   ├── worker_pool.py          # Thread pool for message processing
│   └── __init__.py
├── utilities/
│   ├── pylogger.py             # JSON structured logging
│   └── __init__.py
├── __init__.py
└── README.md
```

## Dependencies

- psycopg2-binary: PostgreSQL adapter
- PyMySQL: MySQL adapter
- paho-mqtt: MQTT client
- python-dotenv: Environment variable loading
- pandas: DataFrame operations (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
