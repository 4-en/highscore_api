from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel
import json
import csv
from functools import lru_cache
import os
import argparse
import typing

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--tables", type=str, default="highscores", help="The name of the endpoint and file to store highscores. Use a comma to separate multiple tables.")
    return parser.parse_args()

@lru_cache()
def get_highscores(name: str) -> typing.List[typing.Set[str, int]]:
    """
    Get the highscores from a file.

    Format of the file should be:
    name,score
    """
    highscores = []
    with open(f"{name}.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            highscores.append(row)

    # sort the highscores
    highscores.sort(key=lambda x: x["score"], reverse=True)
    return highscores
        