import os
from datetime import datetime
from typing import Annotated

import mariadb
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import DB, DataDict, DataList


class PutData(BaseModel):
    datetime: datetime
    temperature: float | None
    humidity: float | None

class PutHeader(BaseModel):
    x_authorization: str

load_dotenv()
ORIGINS = os.getenv("ORIGINS")
API_KEY = os.getenv("API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # scheint, als müsste hier die genaue Origin (Protokoll, Adresse,
    # Port) angegeben werden; individuell für jeden Fall.
    allow_origins=ORIGINS if ORIGINS else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User cursor with db.cursor
db = DB()


@app.get("/")
def read_root(
    skip: int = 0,
    limit: int = 10,
    earliest: datetime | None = None,  # earliest timestamp to consider
    latest: datetime | None = None,  # latest timestamp to consider
    sort_by: str | None = None,  # only necessary for sensor readings, not timestamps
    lowest: float | None = None,  # lowest value to consider
    highest: float | None = None,  # highest value to consider
) -> DataList:
    if earliest or latest:
        data = db.get_data_by_datetime(earliest, latest)
    elif sort_by:
        data = db.get_data_by_sensor(sort_by, lowest, highest)
    else:
        data = db.get_data(skip, limit)
    if not data:
        raise HTTPException(status_code=404, detail="Items not found")
    return data

@app.put("/")
def put_new_data(
    headers: Annotated[PutHeader, Header()], data: PutData
) -> DataDict:
    # TODO: Eine Abfrage für den API-Key einbauen, damit nicht jeder wild vor sich hin Daten einfügen kann.
    if not headers.x_authorization or headers.x_authorization != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        data_dict = data.model_dump()
        db.set_data(data_dict)
        return data_dict
    except mariadb.IntegrityError or mariadb.Error as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error")