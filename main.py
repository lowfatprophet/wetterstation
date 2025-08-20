import os
import sys

import mariadb
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

db_config = {
    "host": "localhost",
    "port": 3306,
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PWD"),
    "database": os.getenv("DB_NAME")
}

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}