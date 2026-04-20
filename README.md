[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/rd3t__9M)
# Introduction to Software Systems S26 
## Course Project: Identity-Verified Multiplayer Arena

The assignment is available [here](https://cs6201.github.io/s26/assets/Project.pdf).

[This](https://hackmd.io/@iss-spring-2026/S1WBWzzoWe) is where you can ask questions about it, for which you will receive answers [here](https://hackmd.io/@iss-spring-2026/ryZ_WGzibx).

Good luck, have fun!

## Setup

### Prerequisites
- Docker
- Python 3.13+
- uv

### 1) Start Databases (MySQL + MongoDB)
```bash
docker compose up -d
```

### 2) Install Python Dependencies
```bash
uv sync
```

### 3) Initialize Player Data with Scraper
```bash
uv run scraper/scraper.py
```

### 4) Start Backend Server (HTTP + WebSocket)
```bash
uv run uvicorn backend.main:app --reload
```

The same FastAPI server hosts both HTTP routes and WebSocket routes:
- Lobby WebSocket: /ws/lobby
- Game room WebSocket: /ws/game/{game_id}

## Database Schemas

### MySQL schema (init.sql)
The following tables are defined:

```sql
CREATE TABLE users (
   uid VARCHAR(50) PRIMARY KEY,
   name VARCHAR(100) NOT NULL,
   elo_rating INT DEFAULT 1200,
   is_online BOOLEAN DEFAULT FALSE
);

CREATE TABLE match_history (
   id BIGINT AUTO_INCREMENT PRIMARY KEY,
   game_id VARCHAR(64) NOT NULL UNIQUE,
   p1_uid VARCHAR(50) NOT NULL,
   p2_uid VARCHAR(50) NOT NULL,
   winner_uid VARCHAR(50) NULL,
   is_draw BOOLEAN NOT NULL DEFAULT FALSE,
   forfeit BOOLEAN NOT NULL DEFAULT FALSE,
   p1_rating_before INT NOT NULL,
   p2_rating_before INT NOT NULL,
   p1_rating_after INT NOT NULL,
   p2_rating_after INT NOT NULL,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### MongoDB schema
Database: multictactoe

Collection: images

Document shape:
```json
{
  "uid": "2025xxxxxx",
  "image": "<base64 profile image>"
}
```

## Notes on Database Initialization

- init.sql is mounted into MySQL at container bootstrap time.
- If MySQL data volume already exists from an older run, new table definitions in init.sql are not auto-applied.
- In that case, apply schema changes manually (for example create match_history table) or reset volumes:

```bash
docker compose down -v
docker compose up -d
```

## Runtime Flow

1. Run scraper to populate MySQL users and MongoDB images from batch_data.csv.
2. Start backend.
3. Open /login.html for webcam authentication.
4. Enter lobby and send/accept match invites.
5. Play game in isolated WebSocket room.
6. On game end, Elo is updated and persisted to users, and match result is written to match_history.
7. View global rankings on /leaderboard.html.

## Assumptions

- website_url entries in batch_data.csv are reachable and expose /images/pfp.jpg.
- Facial recognition module is treated as a black box and not modified.
- Session state is in-memory for this project run.
- A user is considered present in the lobby only when connected online via system flow.
- Forfeit is defined as a game WebSocket disconnect before game completion.

## Submission Notes

- Include a PDF containing screenshots of all LLM chats used during development.
- Screenshots must show prompts, outputs, and model used.
- Keep commit history available to demonstrate project progress milestones.

## File Structure

```text
project-ligma/
|-- docker-compose.yml
|-- init.sql
|-- batch_data.csv
|-- pyproject.toml
|-- scraper/
|   `-- scraper.py
|-- backend/
|   |-- main.py
|   |-- auth.py
|   |-- lobby.py
|   |-- game.py
|   |-- elo.py
|   |-- database.py
|   `-- session.py
|-- frontend/
|   |-- login.html
|   |-- lobby.html
|   |-- game.html
|   `-- leaderboard.html
`-- utils/
   `-- facial_recognition_module.py
```