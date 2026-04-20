from typing import Optional, List
import uuid

class GameSession:
    def __init__(self, p1_uid: str, p2_uid: str):
        self.id = str(uuid.uuid4())
        self.p1 = p1_uid
        self.p2 = p2_uid
        self.board = [None] * 9  # 0-8 slots
        self.turn = p1_uid
        self.winner = None
        self.is_draw = False

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
        elif None not in self.board:
            self.is_draw = True
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

    def to_dict(self):
        return {
            "game_id": self.id,
            "p1": self.p1,
            "p2": self.p2,
            "board": self.board,
            "turn": self.turn,
            "winner": self.winner,
            "is_draw": self.is_draw
        }

active_games: dict[str, GameSession] = {}
