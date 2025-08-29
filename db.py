import os
from contextlib import contextmanager
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

    @contextmanager
    def _db_connection(self):
        """
        Yields a database connection.  
        Until there is a better solution in sight, every request made to the database
        management is bound to make a new connection to MariaDB and to create a new
        cursor. This should change in the future. But for now, this is the implementation.
        """
        yield mariadb.connect(**DB_CONFIG)
        

    @contextmanager
    def _db_cursor(self):
        # https://stackoverflow.com/questions/78726500/a-good-way-of-managing-connections-and-cursors-with-python-using-the-mariadb-con78726617#78726617
        with self._db_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    yield cursor
                except mariadb.Error:
                    conn.rollback()
                finally:
                    conn.commit()
                    if not cursor.closed:
                        cursor.close()
                    conn.close()
        
    def _dictify(self, data: list[Any]) -> DataList:
        """
        Converts a list given as the yielded result of a cursor into the predefined
        DataList object.
        
        :param data: The data list yielded from a cursor.
        :type data: list[Any]
        :return: The given data converted into formatted dictionary.
        :rtype: DataList
        """
        return [
            {
                "datetime": row[1],
                "temperature": row[2],
                "humidity": row[3]
            } for row in data
        ] if data else []

    def _query_builder(
        self, column: str, min: Any | None = None, max: Any | None = None
    ) -> str:
        """
        Creates a SQL query string based on the given filter settings.
        
        :param column: The column to apply the min/max filter to.
        :type column: str
        :param min: The lower bound.
        :type min: Any | None
        :param max: The upper bound.
        :type max: Any | None
        :return: The query string.
        :rtype: str
        """
        query = f"SELECT * FROM {self.table}"
        if min or max:
            query += " WHERE"
        if min:
            query += f" {column} >= {min}"
        if min and max:
            query += " AND"
        if max:
            query += f" {column} < {max}"

        query += " ORDER BY datetime DESC"

        return query

    def _prepare_data(self, value: datetime | float) -> str | float:
        """
        Convert Python's datetime objects to strings and round float values
        so that there are no 15.000008 values around.
        
        :param self: Beschreibung
        :param value: Beschreibung
        :type value: datetime | float
        :return: Beschreibung
        :rtype: str | float
        """
        return str(value) if isinstance(value, datetime) else round(float(value), 1)

    def set_data(self, data: DataDict) -> None:
        """
        Sets a new row of data in the table.
        
        :param data: New set of data. Has to comply to the table's row specification.
        :type data: DataDict
        """
        # Einfügen
        # INSERT INTO messdaten (datetime, temperature, humidity) VALUES ('2025-08-20 12:25:00', 25.7, 41.1);
        with self._db_cursor() as cursor:
            keys = [str(key) for key in list(data.keys())]
            values = [f'"{self._prepare_data(value)}"' for value in list(data.values())]
            insert_query = f"INSERT INTO {self.table} ({','.join(keys)}) VALUES ({','.join(values)})"

            try:
                cursor.execute(insert_query)
            except mariadb.IntegrityError as e:
                print(f"Error inserting data (might be duplicate timestamp): {e}")
                raise mariadb.IntegrityError

    def get_data(self, skip: int = 0, limit: int | None = None) -> DataList:
        """
        The default way to fetch data from the table. Sorts by datetime.
        
        :param skip: The lower limit (how many rows to skip).
        :type skip: int
        :param limit: The upper limit (how many rows to consider).
        :type limit: int | None
        :return: A list of rows filtered by skipped values and an upper limit.
        :rtype: DataList
        """
        # Abrufen
        # SELECT * FROM messdaten ORDER BY datetime DESC LIMIT 3;
        with self._db_cursor() as cursor:
            select_query = f"SELECT * FROM {self.table} ORDER BY datetime DESC"
            if skip > 0:
                select_query += f" OFFSET {skip} ROWS"
                if limit:
                    select_query += f" FETCH {limit} ROWS ONLY"
            elif limit and limit > 0:
                select_query += f" LIMIT {limit}"

            cursor.execute(select_query)
            
            return self._dictify(cursor)

    def get_data_by_datetime(
        self, earliest: datetime | None = None, latest: datetime | None = None
    ) -> DataList:
        """
        Get rows by datetime. Filter by earliest and latest date and time.
        
        :param earliest: The lower boundary to filter.
        :type earliest: datetime | None
        :param latest: The upper boundary to filter.
        :type latest: datetime | None
        :return: A list of rows whose datetime lies between the earliest and the latest given datetime to filter.
        :rtype: DataList
        """
        with self._db_cursor() as cursor:
            select_query = self._query_builder(
                "datetime",
                f"'{earliest}'" if earliest else None,
                f"'{latest}'" if latest else None
            )
            cursor.execute(select_query)

            return self._dictify(cursor)

    def get_data_by_sensor(
        self, column: str, lowest: float | None = None, highest: float | None = None
    ) -> DataList | None:
        """
        Get rows filtered by specified sensor data values. Sorted by datetime.

        :param column: The column to take the data for comparison from.
        :type column: str
        :param lowest: The lower boundary to filter.
        :type lowest: float | None
        :param highest: The upper boundary to filter.
        :type highest: float | None
        :return: A list of values fitting the filter, sorted by datetime.
        :rtype: DataList
        """
        with self._db_cursor() as cursor:
            select_query = self._query_builder(column, lowest, highest)
            cursor.execute(select_query)

            return self._dictify(cursor)