from collections import defaultdict
from typing import Optional
import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from backend.elo import update_elo
from backend.session import get_uid_from_websocket


router = APIRouter()

class GameSession:
    def __init__(self, p1_uid: str, p2_uid: str, p1_name: str = "PILOT_01", p2_name: str = "PILOT_02"):
        self.id = str(uuid.uuid4())
        self.p1 = p1_uid
        self.p1_name = p1_name
        self.p2 = p2_uid
        self.p2_name = p2_name
        self.board = [None] * 9  # 0-8 slots
        self.turn = p1_uid
        self.winner = None
        self.is_draw = False
        self.finished = False
        self.elo_applied = False
        self.match_record_saved = False
        self.forfeit = False
        self.p1_rating_before = None
        self.p2_rating_before = None
        self.p1_rating_after = None
        self.p2_rating_after = None

    def make_move(self, uid: str, position: int) -> bool:
        if self.winner or self.is_draw:
            return False
        if self.turn != uid:
            return False
        if not (0 <= position <= 8) or self.board[position] is not None:
            return False

        mark = 'X' if uid == self.p1 else 'O'
        self.board[position] = mark
        
        if self.check_win(mark):
            self.winner = uid
            self.finished = True
        elif None not in self.board:
            self.is_draw = True
            self.finished = True
        else:
            self.turn = self.p2 if uid == self.p1 else self.p1
        
        return True

    def check_win(self, mark: str) -> bool:
        winning_combos = [
            (0,1,2), (3,4,5), (6,7,8), # rows
            (0,3,6), (1,4,7), (2,5,8), # cols
            (0,4,8), (2,4,6)           # diags
        ]
        return any(all(self.board[i] == mark for i in combo) for combo in winning_combos)

    def calculate_elo_updates(self, p1_rating, p2_rating):
        """Returns (new_p1, new_p2, change_p1, change_p2)"""
        if self.is_draw:
            res = "draw"
        elif self.winner == self.p1:
            res = "win"
        else:
            res = "loss"
        
        new_p1, new_p2 = update_elo(p1_rating, p2_rating, res)
        return new_p1, new_p2, new_p1 - p1_rating, new_p2 - p2_rating

    def to_dict(self):
        return {
            "game_id": self.id,
            "p1": self.p1,
            "p1_name": self.p1_name,
            "p2": self.p2,
            "p2_name": self.p2_name,
            "board": self.board,
            "turn": self.turn,
            "winner": self.winner,
            "is_draw": self.is_draw,
            "finished": self.finished,
            "forfeit": self.forfeit,
            "elo_updates": getattr(self, "elo_updates", None)
        }

    def opponent_of(self, uid: str) -> Optional[str]:
        if uid == self.p1:
            return self.p2
        if uid == self.p2:
            return self.p1
        return None

active_games: dict[str, GameSession] = {}
game_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)


def is_user_in_unfinished_game(uid: str) -> bool:
    for game in active_games.values():
        if not game.finished and uid in (game.p1, game.p2):
            return True
    return False


async def broadcast_game_state(game: GameSession):
    players = game_connections.get(game.id, {})
    payload = {
        "type": "game_state",
        **game.to_dict(),
    }
    for uid, socket in list(players.items()):
        try:
            await socket.send_json(
                {
                    **payload,
                    "you": uid,
                    "your_mark": "X" if uid == game.p1 else "O",
                }
            )
        except Exception:
            pass


async def _apply_elo(mysql_pool, game: GameSession):
    if game.elo_applied:
        return

    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT uid, elo_rating FROM users WHERE uid IN (%s, %s)", (game.p1, game.p2))
            rows = await cur.fetchall()
            ratings = {row[0]: row[1] for row in rows}

            if game.p1 not in ratings or game.p2 not in ratings:
                return

            p1_rating = ratings[game.p1]
            p2_rating = ratings[game.p2]
            game.p1_rating_before = p1_rating
            game.p2_rating_before = p2_rating

            new_p1, new_p2, diff1, diff2 = game.calculate_elo_updates(p1_rating, p2_rating)
            game.elo_updates = {game.p1: diff1, game.p2: diff2}
            game.p1_rating_after = new_p1
            game.p2_rating_after = new_p2

            await cur.execute("UPDATE users SET elo_rating = %s WHERE uid = %s", (new_p1, game.p1))
            await cur.execute("UPDATE users SET elo_rating = %s WHERE uid = %s", (new_p2, game.p2))
        await conn.commit()

    game.elo_applied = True


async def _persist_match_record(mysql_pool, game: GameSession):
    if game.match_record_saved:
        return

    if not game.elo_applied:
        return

    if None in (game.p1_rating_before, game.p2_rating_before, game.p1_rating_after, game.p2_rating_after):
        return

    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO match_history (
                    game_id,
                    p1_uid,
                    p2_uid,
                    winner_uid,
                    is_draw,
                    forfeit,
                    p1_rating_before,
                    p2_rating_before,
                    p1_rating_after,
                    p2_rating_after
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    winner_uid = VALUES(winner_uid),
                    is_draw = VALUES(is_draw),
                    forfeit = VALUES(forfeit),
                    p1_rating_before = VALUES(p1_rating_before),
                    p2_rating_before = VALUES(p2_rating_before),
                    p1_rating_after = VALUES(p1_rating_after),
                    p2_rating_after = VALUES(p2_rating_after),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    game.id,
                    game.p1,
                    game.p2,
                    game.winner,
                    game.is_draw,
                    game.forfeit,
                    game.p1_rating_before,
                    game.p2_rating_before,
                    game.p1_rating_after,
                    game.p2_rating_after,
                ),
            )
        await conn.commit()

    game.match_record_saved = True


async def conclude_game(game: GameSession, mysql_pool):
    if not game.finished:
        return
    await _apply_elo(mysql_pool, game)
    await _persist_match_record(mysql_pool, game)
    await broadcast_game_state(game)

    players = game_connections.get(game.id, {})
    for socket in list(players.values()):
        try:
            await socket.send_json({"type": "game_over", **game.to_dict()})
        except Exception:
            pass


@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str):
    try:
        uid = get_uid_from_websocket(websocket)
    except HTTPException:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    game = active_games.get(game_id)
    if not game:
        await websocket.send_json({"type": "error", "message": "Game not found"})
        await websocket.close(code=4404)
        return

    if uid not in (game.p1, game.p2):
        await websocket.send_json({"type": "error", "message": "Not a participant in this game"})
        await websocket.close(code=4403)
        return

    game_connections[game_id][uid] = websocket
    await broadcast_game_state(game)

    mysql_pool = websocket.app.state.mysql

    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") != "move":
                await websocket.send_json({"type": "error", "message": "Unsupported message"})
                continue

            if game.finished:
                await websocket.send_json({"type": "error", "message": "Game already finished"})
                continue

            position = message.get("position")
            if not isinstance(position, int):
                await websocket.send_json({"type": "error", "message": "Position must be an integer"})
                continue

            success = game.make_move(uid, position)
            if not success:
                await websocket.send_json({"type": "error", "message": "Invalid move"})
                continue

            await broadcast_game_state(game)

            if game.finished:
                await conclude_game(game, mysql_pool)

    except WebSocketDisconnect:
        pass
    finally:
        game_connections[game_id].pop(uid, None)

        if not game.finished:
            opponent_uid = game.opponent_of(uid)
            if opponent_uid:
                game.winner = opponent_uid
                game.forfeit = True
                game.finished = True
                game.is_draw = False
                game.turn = None
                await conclude_game(game, mysql_pool)

        if game.finished and not game_connections.get(game_id):
            active_games.pop(game_id, None)
            game_connections.pop(game_id, None)
