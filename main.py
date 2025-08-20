import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from db import DB


class PutData(BaseModel):
    datetime: datetime
    temperature: float | None
    humidity: float | None

app = FastAPI()

# User cursor with db.cursor
db = DB()

load_dotenv()
API_KEY = os.getenv("API_KEY")

@app.get("/")
def read_root():
    response = db.get_data()
    if not response:
        raise HTTPException(status_code=404, detail="Items not found")
    return response

@app.put("/")
def put_new_data(data: PutData) -> Any:
    # TODO: Eine Abfrage für den API-Key einbauen, damit nicht jeder wild vor sich hin Daten einfügen kann.
    # Als extra Header-Feld?
    try:
        db.set_data(data.model_dump())
        return data.model_dump()
    except:  # noqa: E722
        # Das kann man wohl auch eleganter lösen
        raise HTTPException(status_code=500, detail="Internal Server Error")
    