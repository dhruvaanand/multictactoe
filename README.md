[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/rd3t__9M)
# Introduction to Software Systems S26 
## Course Project: Identity-Verified Multiplayer Arena

The assignment is available [here](https://cs6201.github.io/s26/assets/Project.pdf).

[This](https://hackmd.io/@iss-spring-2026/S1WBWzzoWe) is where you can ask questions about it, for which you will receive answers [here](https://hackmd.io/@iss-spring-2026/ryZ_WGzibx).

Good luck, have fun!

## Setup & File Structure

### Prerequisites
- Docker
- Python 3.11+ with `uv`

### Getting Started

1. **Start databases**
```bash
   docker compose up -d
```

2. **Install dependencies**
```bash
   uv sync
```

3. **Run the scraper**
```bash
   uv run scraper/scraper.py
```

4. **Start the server**
```bash
   uv run uvicorn backend.main:app --reload
```

### File Structure
```
multictactoe/
├── docker-compose.yml        # MySQL + MongoDB services
├── init.sql                  # Database schema (auto-run on first start)
├── batch_data.csv            # Student roster
├── pyproject.toml            # Dependencies
├── scraper/
│   └── scraper.py            # Async image harvester
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── auth.py               # Facial recognition login
│   ├── lobby.py              # WebSocket presence system
│   ├── game.py               # Tic-tac-toe game logic
│   ├── elo.py                # Elo rating calculations
│   └── database.py           # Database connections
├── frontend/
│   ├── login.html
│   ├── lobby.html
│   ├── game.html
│   └── leaderboard.html
└── utils/
    └── facial_recognition_module.py   # Provided — do not modify
```