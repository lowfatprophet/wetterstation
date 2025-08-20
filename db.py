import os
from datetime import datetime

import mariadb
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv("DB_PORT")
DB_CONFIG = {
    "host": "localhost",
    "port": int(PORT) if PORT else 3306,
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PWD"),
    "database": os.getenv("DB_NAME")
}

class DB:
    def __init__(self):
        self.table = "messdaten"

        try:
            self.conn = mariadb.connect(**DB_CONFIG)

            self.cursor = self.conn.cursor()
        except mariadb.Error as e:
            raise e
        
    def __del__(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def connect(self):
        if self.conn and self.cursor:
            return
        try:
            self.conn = mariadb.connect(**DB_CONFIG)

            self.cursor = self.conn.cursor()
        except mariadb.Error as e:
            raise e

    def set_data(self, data):
        self.connect()
        # Einfügen
        # INSERT INTO messdaten (datetime, temperature, humidity) VALUES ('2025-08-20 12:25:00', 25.7, 41.1);
        keys = [str(key) for key in list(data.keys())]
        values = [f'"{str(value)}"' for value in list(data.values())]
        insert_query = f"INSERT INTO {self.table} ({','.join(keys)}) VALUES ({','.join(values)})"

        try:
            self.cursor.execute(insert_query)
            self.conn.commit()
        except mariadb.IntegrityError as e:
            print(f"Error inserting data (might be duplicate timestamp): {e}")
        except mariadb.Error as e:
            print(f"Error inserting data: {e}")
            self.conn.rollback()

    def get_data(
            self, oldest: datetime | None = None, newest: datetime | None = None
        ) -> dict[datetime, dict[str, float]]:
        self.connect()
        # Abrufen
        # SELECT * FROM messdaten LIMIT 3;
        select_query = f"SELECT * FROM {self.table}"
        if oldest or newest:
            select_query += " WHERE"
        if oldest:
            select_query += f" datetime >= '{oldest}'"
        if oldest and newest:
            select_query += " AND"
        if newest:
            select_query += f" datetime < '{newest}'"
        self.cursor.execute(select_query)
        
        return {
            row[1]: {"temperature": row[2], "humidity": row[3]}
            for row in self.cursor
        }