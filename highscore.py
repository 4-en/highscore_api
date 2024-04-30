# Description: A simple highscore API that allows you to save and retrieve highscores.

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
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
    parser.add_argument("--tables", type=str, default="highscores", help="The name of the endpoint and file to store highscores. Use a comma to separate multiple tables.")
    parser.add_argument("--size", type=int, default=100, help="The number of highscores to store.")
    return parser.parse_args()

@lru_cache()
def get_highscores(name: str) -> typing.List[typing.Dict[str, int]]:
    """
    Get the highscores from a file.

    Format of the file should be:
    name,score
    """
    highscores = []

    if not os.path.exists(f"{name}.csv"):
        update_highscores(name, [])
        return highscores

    with open(f"{name}.csv", "r") as file:
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
    with open(f"{name}.csv", "w") as file:
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

class Highscores(BaseModel):
    name: str
    highscores: typing.List[Score]

def check_table(name: str):
    if not name in tables:
        raise HTTPException(status_code=404, detail="Table not found")

@app.get("/highscore/{name}", response_model=Highscores)
def get_highscore(name: str):
    name = name.lower()
    check_table(name)
    
    highscores = get_highscores(name)
    highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
    return highscore_response

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