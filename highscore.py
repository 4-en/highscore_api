# Description: A simple highscore API that allows you to save and retrieve highscores.

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, Response
import uvicorn
from pydantic import BaseModel
import csv
from functools import lru_cache
import os
import argparse
import typing
from hashlib import sha256
import time


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--tables", type=str, default="main", help="The name of the endpoint and file to store highscores. Use a comma to separate multiple tables.")
    parser.add_argument("--size", type=int, default=100, help="The number of highscores to store.")
    parser.add_argument("--use_secret", action="store_true", help="Use a (very naive) secret key to verify the highscore. The key is sha256(\"name-UwU-score\").hexstring().")
    parser.add_argument("--salt", type=str, default="-UwU-", help="The salt to use for the secret key.")
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
            highscores.append({"name": row["name"], "score": int(row["score"]), "time": row["time"]})

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
        writer = csv.DictWriter(file, fieldnames=["name", "score", "time"], lineterminator="\n", delimiter=",")
        writer.writeheader()
        for row in highscores:
            writer.writerow(row)

args = get_args()
tables = args.tables.split(",")
tables = [table.strip().lower() for table in tables]

def calc_secret_key(name: str, score: int) -> str:
    return sha256(f"{name}{args.salt}{score}".encode()).hexdigest()

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

import markdown   
@lru_cache()
def get_root_html():
    md = ""
    with open("README.md", "r") as f:
        md = f.read()
    
    insert = "[Repository](https://github.com/4-en/highscore_api) | [API Documentation](/docs) | [Swagger UI](/redoc) | "
    get_endpoints = " | ".join([f"[{table}](/highscore/{table})" for table in tables])
    insert += get_endpoints
    # insert after the first line starting with #
    pos = md.find("#")
    pos = md.find("\n", pos)
    md = md[:pos] + "\n" + insert + md[pos:]
    md_html = markdown.markdown(md)

    html = ""
    with open("root.html", "r") as f:
        html = f.read()

    html = html.replace("{{md_html}}", md_html)
    return html
    
@app.get("/")
def read_root():
    return HTMLResponse(content=get_root_html(), status_code=200)


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
        
        highscores.append({"name": score.name, "score": score.score, "time": int(time.time())})
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
        
        highscores.append({"name": score.name, "score": score.score, "time": int(time.time())})
        highscores.sort(key=lambda x: x["score"], reverse=True)
        if len(highscores) > args.size:
            highscores = highscores[:args.size]

        update_highscores(name, highscores)
        get_highscores.cache_clear()
        highscore_response = Highscores(name=name, highscores=[Score(name=score["name"], score=score["score"]) for score in highscores])
        return highscore_response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port)