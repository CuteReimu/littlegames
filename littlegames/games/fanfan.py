# 象棋翻翻棋
import io
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont

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

_FONT_DIRS = {
    "darwin": "/Library/Fonts/",
    "linux": "/usr/share/fonts/",
    "win32": "C:\\Windows\\Fonts\\",
}
_font_dir = _FONT_DIRS.get(sys.platform, "")
_font_path = ""
if _font_dir and os.path.isdir(_font_dir):
    for _root, _, _files in os.walk(_font_dir):
        for _filename in _files:
            if _filename.lower() == "simhei.ttf":
                _font_path = os.path.join(_root, _filename)
                break
        if _font_path:
            break
if not _font_path:
    raise FileNotFoundError(f"找不到 SimHei 字体文件: {_font_dir or sys.platform}")

_font = ImageFont.truetype(_font_path, 50)


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

    def display_board(self) -> bytes:
        """将当前棋盘绘制成 PNG，并返回 PNG 的二进制内容。"""

        # 调整这个值即可等比例调整棋盘大小；例如 64、96、128。
        cell_size = 96
        line_width = max(2, cell_size // 24)
        image = Image.new("RGB", (8 * cell_size, 4 * cell_size), "#f5e6c8")
        draw = ImageDraw.Draw(image)

        font = _font.font_variant(size=int(cell_size * 0.52))

        for x, row in enumerate(self.board):
            for y, col in enumerate(row):
                left, top = y * cell_size, x * cell_size
                right, bottom = left + cell_size, top + cell_size
                if col is None:
                    fill = "#ead8b5"
                elif not col[2]:
                    fill = "#315b7d"
                else:
                    fill = "#fffaf0"
                draw.rectangle((left, top, right, bottom), fill=fill,
                               outline="#4b3621", width=line_width)

                if col is None:
                    continue
                if not col[2]:
                    draw.rectangle(
                        (left + cell_size // 6, top + cell_size // 6,
                         right - cell_size // 6, bottom - cell_size // 6),
                        outline="#d9c18c", width=line_width,
                    )
                    continue

                color, piece, _ = col
                text = _piece_names[piece][color]
                text_color = "#c62828" if color == 0 else "#1565c0"
                draw.text((left + cell_size / 2, top + cell_size / 2), text,
                          font=font, fill=text_color, anchor="mm")

        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

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
        color_from, type_from, _ = piece_from
        if color_from != self.turn:
            return "只能移动自己的棋子"
        if piece_to is not None and not piece_to[2]:
            return "目标位置的棋子未翻开"
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

    # 检查游戏是否结束，返回0表示未结束，1表示uid1获胜，2表示uid2获胜
    def check_game_over(self) -> str:
        red_pieces = sum(1 for row in self.board for col in row if col is not None and col[0] == 0)
        blue_pieces = sum(1 for row in self.board for col in row if col is not None and col[0] == 1)
        if red_pieces == 0 and blue_pieces == 0:
            return "\n\n游戏结束，平局"
        if red_pieces == 0:
            return "\n\n游戏结束，蓝方获胜"
        if blue_pieces == 0:
            return "\n\n游戏结束，红方获胜"
        return ""
