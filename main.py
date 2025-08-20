import os
from datetime import datetime
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from db import DB


class PutData(BaseModel):
    datetime: datetime
    temperature: float | None
    humidity: float | None

class PutHeader(BaseModel):
    x_authorization: str

app = FastAPI()

# User cursor with db.cursor
db = DB()

load_dotenv()
API_KEY = os.getenv("API_KEY")
# Work-around, weil das grad anders nicht funktioniert.
API_KEY = "G3n4<6HR&usaO.s2kWj:Hyw'Bst"

@app.get("/")
def read_root(
        oldest: datetime | None = None, newest: datetime | None = None
    ) -> dict[datetime, dict[str, float]]:
    response = db.get_data(oldest, newest)
    if not response:
        raise HTTPException(status_code=404, detail="Items not found")
    return response

@app.put("/")
def put_new_data(headers: Annotated[PutHeader, Header()], data: PutData) -> Any:
    # TODO: Eine Abfrage für den API-Key einbauen, damit nicht jeder wild vor sich hin Daten einfügen kann.
    if not headers.x_authorization or headers.x_authorization != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    try:
        data_dict = data.model_dump()
        db.set_data(data_dict)
        return data_dict
    except:  # noqa: E722
        # Das kann man wohl auch eleganter lösen
        raise HTTPException(status_code=500, detail="Internal Server Error")
    