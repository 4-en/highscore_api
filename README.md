# Highscore API

## Description
A simple API developed with FastAPI to save and retrieve highscores. This API allows clients to interact with highscore tables for various games or contexts, providing functionality to get highscores, save new highscores, and check existing highscore tables. It supports an optional security feature that uses a SHA-256 hash to verify the authenticity of the highscores submitted.

## Features
- Retrieve highscores for specific tables using a RESTful endpoint.
- Save new highscores to a table with or without secret key verification.
- List all available highscore tables.
- API documentation automatically generated by FastAPI at the `/docs` endpoint.

## Technologies
- FastAPI for the web framework.
- Uvicorn for the ASGI server.
- Pydantic for data validation.
- CSV for storing highscore data.
- SHA-256 for generating optional secret keys to verify highscores.

## Setup
### Requirements
- Python 3.8 or higher
- FastAPI
- Uvicorn
- markdown

### Installation
1. Clone this repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the server:
   ```
   python highscore.py
   ```

## API Endpoints
- `GET /`: Root endpoint which returns HTML content describing the API.
- `GET /highscores`: List all highscore tables.
- `GET /highscore/{name}`: Get highscores for the specified table.
- `POST /highscore/save/{name}`: Save a highscore to the specified table. When `use_secret` is enabled, this endpoint expects a `VerifiedScore` object; otherwise, it expects a `Score` object.

### Models
- `Score`: Standard score model containing `name` and `score`.
- `VerifiedScore`: Extends `Score` with a `secret` field for verification.
- `Highscores`: Contains a list of `Score` objects and a name for the highscore table.

## Configuration
The server can be configured with several command line arguments:
- `--port`: Set the port number for the server (default is 8080).
- `--tables`: Comma-separated list of table names to initialize on startup.
- `--size`: Maximum number of highscores to store in each table (default is 100).
- `--use_secret`: Enable or disable secret key verification for score submission.
- `--salt`: Set the salt used to calculate the secret.

## Usage
Example of how to interact with the API using `curl`:

### Get highscores
```
curl http://localhost:8080/highscore/sample_table
```

### Save highscore
```
curl -X POST -H "Content-Type: application/json" -d '{"name": "Alice", "score": 5000}' http://localhost:8080/highscore/save/sample_table
```
