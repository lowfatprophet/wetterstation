import os
from datetime import datetime
from typing import Any

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

type DataDict = dict[str, datetime | float]

type DataList = list[DataDict]

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
        
    def dictify(self, data) -> DataList:
        return [
            {
                "datetime": row[1],
                "temperature": row[2],
                "humidity": row[3]
            } for row in data
        ]

    def query_builder(
        self, column: str, min: Any | None = None, max: Any | None = None
    ) -> str:
        query = f"SELECT * FROM {self.table}"
        if min or max:
            query += " WHERE"
        if min:
            query += f" {column} >= {min}"
        if min and max:
            query += " AND"
        if max:
            query += f" {column} < {max}"

        return query

    def set_data(self, data: DataDict) -> None:
        # Einfügen
        # INSERT INTO messdaten (datetime, temperature, humidity) VALUES ('2025-08-20 12:25:00', 25.7, 41.1);
        self.connect()

        keys = [str(key) for key in list(data.keys())]
        values = [f'"{str(value)}"' for value in list(data.values())]
        insert_query = f"INSERT INTO {self.table} ({','.join(keys)}) VALUES ({','.join(values)})"

        try:
            self.cursor.execute(insert_query)
            self.conn.commit()
        except mariadb.IntegrityError as e:
            print(f"Error inserting data (might be duplicate timestamp): {e}")
            raise mariadb.IntegrityError
        except mariadb.Error as e:
            print(f"Error inserting data: {e}")
            self.conn.rollback()
            raise mariadb.Error

    def get_data(self, skip: int = 0, limit: int | None = None) -> DataList:
        # Abrufen
        # SELECT * FROM messdaten LIMIT 3;
        self.connect()

        select_query = f"SELECT * FROM {self.table}"
        if skip > 0:
            select_query += f" OFFSET {skip} ROWS"
            if limit:
                select_query += f" FETCH {limit} ROWS ONLY"
        elif limit and limit > 0:
            select_query += f" LIMIT {limit}"

        self.cursor.execute(select_query)

        return self.dictify(self.cursor)

    def get_data_by_datetime(
        self, earliest: datetime | None = None, latest: datetime | None = None
    ) -> DataList:
        self.connect()
        select_query = self.query_builder(
            "datetime",
            f"'{earliest}'" if earliest else None,
            f"'{latest}'" if latest else None
        )
        self.cursor.execute(select_query)
        return self.dictify(self.cursor)

    def get_data_by_sensor(
        self, column: str, lowest: float | None = None, highest: float | None = None
    ) -> DataList:
        self.connect()
        select_query = self.query_builder(column, lowest, highest)
        self.cursor.execute(select_query)
        return self.dictify(self.cursor)