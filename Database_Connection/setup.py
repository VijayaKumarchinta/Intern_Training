import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg2

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

REQUIRED_ENV_VARS = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_SCHEMA",
    "DB_TABLE",
)

_missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]

if _missing:
    raise RuntimeError(
        "Missing required environment variables: "
        + ", ".join(_missing)
        + ". Copy .env.example to .env and fill in the values."
    )


def _get_int(name):
    try:
        return int(os.getenv(name, ""))
    except ValueError:
        raise RuntimeError(
            f"Environment variable {name} must be an integer, got: {os.getenv(name)!r}"
        ) from None


class Postgremanager:

    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = _get_int("DB_PORT")

        self.db_name = os.getenv("DB_NAME")
        self.schema_name = os.getenv("DB_SCHEMA")
        self.table_name = os.getenv("DB_TABLE")

        self.conn = None
        self.cur = None

    def connect(self, dbname=None):
        target_db = dbname or self.db_name

        if self.conn and not self.conn.closed and self.conn.info.dbname == target_db:
            return

        self.conn = None
        self.cur = None

        try:
            self.conn = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                database=target_db
            )
            self.cur = self.conn.cursor()
            print(f"Connected to Database {target_db}")

        except Exception as e:
            print(f"Connection failed: {e}")
            raise

    def create_db(self):
        self.connect('postgres')
        self.conn.autocommit = True

        try:
            query = f"CREATE DATABASE {self.db_name}"
            self.cur.execute(query)
            self.conn.commit()
            print(f"Database '{self.db_name}' is created successfully.")
        except Exception as e:
            print(f"Error while creating Database: {e}")

    def create_schema(self):
        self.connect(self.db_name)
        query = f"CREATE SCHEMA IF NOT EXISTS {self.schema_name}"

        try:
            self.cur.execute(query)
            self.conn.commit()
            print(f"Schema '{self.schema_name}' created successfully.")
        except Exception as e:
            print(f"Error while creating schema: {e}")

    def create_table(self):
        self.connect(self.db_name)
        query = f"""CREATE TABLE IF NOT EXISTS {self.schema_name}.{self.table_name}  (
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone BIGINT,
            hire_date DATE NOT NULL DEFAULT CURRENT_DATE
            )"""
        
        try:
            self.cur.execute(query)
            self.conn.commit()
            print(f"Table '{self.table_name}' created successfully.")
        except Exception as e:
            print(f"Error while creating table: {e}")

    def insert_employee(self, data):
        self.connect()
        query = f"""
            INSERT INTO {self.schema_name}.{self.table_name}
            (first_name, last_name, email, phone, hire_date)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            count = 0
            for emp in data:
                self.cur.execute(query, (
                    emp['first_name'],
                    emp['last_name'],
                    emp['email'],
                    emp['phone'],
                    emp['hire_date']
                ))
                count += 1
                print(f"Employee '{emp['first_name']} {emp['last_name']}' inserted.")
            self.conn.commit()
            print(f"{count} employee(s) inserted successfully.")
            return count
        except Exception as e:
            print(f"Error while inserting employee(s): {e}")
            if self.conn:
                self.conn.rollback()
            return 0

    def update_employee(self, email, data):
        self.connect()
        allowed = ['first_name', 'last_name', 'email', 'phone', 'hire_date']

        parts = []
        values = []
        for field in allowed:
            if field in data:
                parts.append(f"{field} = %s")
                values.append(data[field])

        if not parts:
            print("No valid fields to update.")
            return False
        
        values.append(email)
        query = f"UPDATE {self.schema_name}.{self.table_name} SET {', '.join(parts)} WHERE email = %s"

        try:
            self.cur.execute(query, values)
            self.conn.commit()

            new_email = data.get('email', email)
            if self.cur.rowcount > 0:
                print(f"Employee '{email}' updated to '{new_email}' successfully.")
                return True
            else:
                print(f"Employee '{email}' not found.")
                return False

        except Exception as e:
            print(f"Error while updating employee: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def delete_employee(self, email):
        self.connect()
        query = f"""
            DELETE FROM {self.schema_name}.{self.table_name}
            WHERE email = %s
        """
        try:
            self.cur.execute(query, (email,))
            self.conn.commit()

            if self.cur.rowcount > 0:
                print(f"Employee '{email}' deleted successfully.")
                return True
            else:
                print(f"Employee '{email}' not found.")
                return False

        except Exception as e:
            print(f"Error while deleting employee: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def fetch_all_employees(self):
        self.connect()
        query = f"SELECT * FROM {self.schema_name}.{self.table_name}"

        try:
            self.cur.execute(query)
            rows = self.cur.fetchall()
            employees = []
            for row in rows:
                employees.append({
                    'first_name': row[0],
                    'last_name': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'hire_date': str(row[4])
                })
            return employees

        except Exception as e:
            print(f"Fetching data failed: {e}")
            return []


if __name__ == "__main__":
    db = Postgremanager()
    try:
        db.create_db()
        db.create_schema()
        db.create_table()
        employees = db.fetch_all_employees()
        for emp in employees:
            print(emp)
    except Exception as e:
        print(f"Operation failed : {e}")
