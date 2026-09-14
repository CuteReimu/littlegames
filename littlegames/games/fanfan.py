# 象棋翻翻棋
import random

_将 = 10
_士 = 9
_象 = 8
_马 = 7
_车 = 6
_炮 = 5
_兵 = 4

_piece_names = {
    _将: ("帅", "将"),
    _士: ("仕", "士"),
    _象: ("相", "象"),
    _车: ("车", "車"),
    _马: ("马", "馬"),
    _炮: ("炮", "砲"),
    _兵: ("兵", "卒"),
}


class FanFan:
    def __init__(self, uid1: str, uid2: str):
        self.uid1 = uid1
        self.uid2 = uid2
        self.turn = 0  # 0表示uid1的回合，1表示uid2的回合
        self.board = FanFan._init_board()

    def current_player(self) -> str:
        return self.uid1 if self.turn == 0 else self.uid2

    @staticmethod
    def _init_board():
        chess: list[int] = [_将, _士, _士, _象, _象, _马, _马, _车, _车, _炮, _炮, _兵, _兵, _兵, _兵, _兵]
        chess_pieces: list[tuple[int, int, bool] | None] = \
            [(color, piece, False) for color in (0, 1) for piece in chess]
        random.shuffle(chess_pieces)
        return [chess_pieces[i:i + 8] for i in range(0, 32, 8)]

    def display_board(self) -> str:
        display = []
        for row in self.board:
            display_row = []
            for col in row:
                if col is None:
                    display_row.append("□")
                    continue
                color, piece, revealed = col
                if revealed:
                    # color_name = "**" if color == 0 else "*"
                    # display_row.append(f"{color_name}{_piece_names[piece][color]}{color_name}")
                    color_name = "red" if color == 0 else "blue"
                    display_row.append(r"$\textcolor{" + color_name + "}{" + _piece_names[piece][color] + "}$")
                else:
                    display_row.append("■")
            display.append(" ".join(display_row))
        return "\n".join(display)

    def fan(self, uid: str, x: int, y: int) -> str:
        if uid not in (self.uid1, self.uid2):
            return "你不在游戏中"
        if (self.turn == 0 and uid != self.uid1) or (self.turn == 1 and uid != self.uid2):
            return "现在不是你的回合"
        if not (0 <= x < 4 and 0 <= y < 8):
            return "坐标超出范围"
        piece = self.board[x][y]
        if piece is None:
            return "该位置没有棋子"
        color, piece_type, revealed = piece
        if revealed:
            return "该棋子已经被翻开"
        self.board[x][y] = (color, piece_type, True)
        self.turn = 1 - self.turn
        return f"翻开了 {('红', '蓝')[color]}{_piece_names[piece_type][color]}"

    def move(self, uid: str, x1: int, y1: int, x2: int, y2: int) -> str:
        if uid not in (self.uid1, self.uid2):
            return "你不在游戏中"
        if (self.turn == 0 and uid != self.uid1) or (self.turn == 1 and uid != self.uid2):
            return "现在不是你的回合"
        if not (0 <= x1 < 4 and 0 <= y1 < 8 and 0 <= x2 < 4 and 0 <= y2 < 8):
            return "坐标超出范围"
        piece_from = self.board[x1][y1]
        piece_to = self.board[x2][y2]
        if piece_from is None or not piece_from[2]:
            return "起始位置没有翻开的棋子"
        if piece_to is not None and not piece_to[2]:
            return "目标位置的棋子未翻开"
        color_from, type_from, _ = piece_from
        if color_from != self.turn:
            return "只能移动自己的棋子"
        if type_from == _炮:  # 炮的特殊吃法
            if piece_to is None:
                if abs(x1 - x2) + abs(y1 - y2) != 1:
                    return "只能移动到相邻的空格"
            else:
                if x1 == x2:
                    count = sum(1 for y in range(min(y1, y2) + 1, max(y1, y2)) if self.board[x1][y] is not None)
                elif y1 == y2:
                    count = sum(1 for x in range(min(x1, x2) + 1, max(x1, x2)) if self.board[x][y1] is not None)
                else:
                    return "炮只能沿直线移动"
                if count != 1:
                    return "炮吃子时必须隔一个棋子"
        elif abs(x1 - x2) + abs(y1 - y2) != 1:
            return "只能移动到相邻的空格"
        msg = f"{('红', '蓝')[color_from]}{_piece_names[type_from][color_from]} 移动了"
        # 检查是否可以吃掉目标棋子
        if piece_to is not None:
            color_to, type_to, _ = piece_to
            if color_from == color_to:
                return "不能吃掉自己的棋子"
            # 检查吃子规则
            capture_result = self._can_capture(type_from, type_to)
            if capture_result < 0:
                return f"{_piece_names[type_from][color_from]}不能吃掉{_piece_names[type_to][color_to]}"
            elif capture_result == 0:
                self.board[x2][y2] = None
                self.board[x1][y1] = None
                self.turn = 1 - self.turn
                msg += f"，{_piece_names[type_from][color_from]}与{_piece_names[type_to][color_to]}同归于尽"
                return msg
            else:
                msg += f"，吃掉了 {('红', '蓝')[color_to]}{_piece_names[type_to][color_to]}"
        # 移动棋子
        self.board[x2][y2] = piece_from
        self.board[x1][y1] = None
        self.turn = 1 - self.turn
        return msg

    # 检查是否可以吃掉目标棋子，大于0表示可以吃掉，小于0表示不能吃掉，等于0表示同归于尽
    @staticmethod
    def _can_capture(type_from: int, type_to: int) -> int:
        if type_from == _炮:  # 炮的隔子吃法，可以吃掉任何棋子
            return 1
        if type_from == _兵 and type_to == _将:
            return 1
        if type_from == _将 and type_to == _兵:
            return -1
        return type_from - type_to
