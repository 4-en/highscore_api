# Description: A simple highscore API that allows you to save and retrieve highscores.

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
from pydantic import BaseModel
import json
import csv
from functools import lru_cache
import os
import argparse
import typing
from hashlib import sha256

def calc_secret_key(name: str, score: int) -> str:
    return sha256(f"{name}-UwU-{score}".encode()).hexdigest()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--tables", type=str, default="main", help="The name of the endpoint and file to store highscores. Use a comma to separate multiple tables.")
    parser.add_argument("--size", type=int, default=100, help="The number of highscores to store.")
    parser.add_argument("--use_secret", action="store_true", help="Use a (very naive) secret key to verify the highscore. The key is sha256(\"name-UwU-score\").hexstring().")
    return parser.parse_args()

@lru_cache()
def get_highscores(name: str) -> typing.List[typing.Dict[str, int]]:
    """
    Get the highscores from a file.

    Format of the file should be:
    name,score
    """
    highscores = []

    path = f"tables/{name}.csv"

    if not os.path.exists(path):
        update_highscores(name, [])
        return highscores

    with open(path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            highscores.append({"name": row["name"], "score": int(row["score"])})

    # sort the highscores
    highscores.sort(key=lambda x: x["score"], reverse=True)
    return highscores

def update_highscores(name: str, highscores: typing.List[typing.Dict[str, int]]):
    """
    Update the highscores in a file.

    Format of the file should be:
    name,score
    """

    path = f"tables/{name}.csv"
    # make sure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "score"], lineterminator="\n", delimiter=",")
        writer.writeheader()
        for row in highscores:
            writer.writerow(row)

args = get_args()
tables = args.tables.split(",")
tables = [table.strip().lower() for table in tables]

app = FastAPI()

class Score(BaseModel):
    name: str
    score: int

class VerifiedScore(Score):
    secret: str

class Highscores(BaseModel):
    name: str
    highscores: typing.List[Score]

def check_table(name: str):
    if not name in tables:
        raise HTTPException(status_code=404, detail="Table not found")
    
@app.get("/")
def read_root():
    str = """
        <html>
        <head>
        <title>Highscore API</title>
        </head>
        <body>
        <h1>Highscore API</h1>
        <p>Use the /highscore/{name} endpoint to get the highscores for a specific table.</p>
        <p>Use the /highscore/save/{name} endpoint to save a highscore to a specific table.</p>
        <p>Use the /highscores endpoint to get a list of all tables.</p>
        <br>
        <p>Use the /docs endpoint to see the API documentation.</p>
        </body>
        </html>
        """.strip()
    # return as HTML
    return HTMLResponse(content=str)

@app.get("/highscores", response_model=typing.List[str])
def get_tables():
    return tables

@app.get("/highscore/{name}", response_model=Highscores)
def get_highscore(name: str):
    name = name.lower()
    check_table(name)
    
    highscores = get_highscores(name)
    highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
    return highscore_response

if args.use_secret:
    @app.post("/highscore/save/{name}", response_model=Highscores)
    def save_highscore(name: str, score: VerifiedScore):
        name = name.lower()
        check_table(name)

        if score.secret != calc_secret_key(score.name, score.score):
            return JSONResponse(status_code=403, content={"message": "Invalid secret key."})

        highscores = get_highscores(name)
        lowest_score = highscores[-1]["score"] if len(highscores) > 0 else 0
        if score.score <= lowest_score and len(highscores) >= args.size:
            highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
            return highscore_response
        
        highscores.append({"name": score.name, "score": score.score})
        highscores.sort(key=lambda x: x["score"], reverse=True)
        if len(highscores) > args.size:
            highscores = highscores[:args.size]

        update_highscores(name, highscores)
        get_highscores.cache_clear()
        highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
        return highscore_response
else:
    @app.post("/highscore/save/{name}", response_model=Highscores)
    def save_highscore(name: str, score: Score):
        name = name.lower()
        check_table(name)

        highscores = get_highscores(name)
        lowest_score = highscores[-1]["score"] if len(highscores) > 0 else 0
        if score.score <= lowest_score and len(highscores) >= args.size:
            highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
            return highscore_response
        
        highscores.append({"name": score.name, "score": score.score})
        highscores.sort(key=lambda x: x["score"], reverse=True)
        if len(highscores) > args.size:
            highscores = highscores[:args.size]

        update_highscores(name, highscores)
        get_highscores.cache_clear()
        highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
        return highscore_response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port)