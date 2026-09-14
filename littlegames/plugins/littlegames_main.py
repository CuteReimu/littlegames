"""littlegames 主插件 - NoneBot2 命令路由"""
from nonebot import on_command
from nonebot.adapters import Event
from nonebot.adapters.qq.message import MessageSegment, MentionUser
from nonebot.log import logger
from nonebot.params import CommandArg

from ..games.fanfan import FanFan
from ..utils import at_user, input_link

logger.opt(colors=True).info("<green>✅ littlegames_main 插件加载成功！</green>")

fanfan_games: dict[str, FanFan] = {}

# ---- 象棋翻翻棋 ----
_fanfan_start_cmd = on_command("象棋翻翻棋", priority=10, block=True)


@_fanfan_start_cmd.handle()
async def _handle_fanfan_start(event: Event, args=CommandArg()):
    uid2: str | None = None
    for arg in args:
        if isinstance(arg, MentionUser):
            uid2 = arg.data["user_id"]
            break
    if uid2 is None:
        await _fanfan_start_cmd.finish("命令格式：\n/象棋翻翻棋 @对手")
        return
    uid1 = event.get_user_id()
    if uid1 == uid2:
        await _fanfan_start_cmd.finish("你不能和自己玩")
        return
    if uid1 in fanfan_games or uid2 in fanfan_games:
        await _fanfan_start_cmd.finish("你或对手已经在游戏中，请先结束当前游戏")
        return
    game = FanFan(uid1, uid2)
    fanfan_games[uid1] = game
    fanfan_games[uid2] = game
    ret = f"游戏开始！\n"
    ret += f"红方：{at_user(uid1)}\n蓝方：{at_user(uid2)}\n由红方先行\n"
    ret += "将＞士＞象＞马＞车＞炮＞兵，但兵能吃将，炮只能隔子吃（隔子吃无视大小）"
    ret += "\n你可以输入：\n"
    ret += f"- {input_link("翻开")} 行号 列号\n"
    ret += f"- {input_link("移动")} 行号 列号 上/下/左/右\n"
    ret += f"- {input_link("移动")} 行号 列号 到 行号 列号\n"
    ret += "\n当前盘面：\n\n---\n\n"
    ret += game.display_board()
    await _fanfan_start_cmd.finish(MessageSegment.markdown(ret))


# ---- 象棋翻翻棋-翻开 ----
_fanfan_fan_cmd = on_command("翻开", priority=10, block=True)


@_fanfan_fan_cmd.handle()
async def _handle_fanfan_fan(event: Event, args=CommandArg()):
    uid = event.get_user_id()
    game = fanfan_games.get(uid)
    if game is None:
        await _fanfan_fan_cmd.finish("你还没有开始游戏，请先使用命令：\n象棋翻翻棋 @对手")
        return
    if uid != game.current_player():
        await _fanfan_fan_cmd.finish(f"现在轮到对方行动")
        return
    arr: str = args.extract_plain_text().strip().replace(" ", "")
    if len(arr) < 2:
        await _fanfan_fan_cmd.finish("命令格式：\n/翻开 行号 列号")
        return
    try:
        x = int(arr[0]) - 1
        y = int(arr[1]) - 1
    except ValueError:
        await _fanfan_fan_cmd.finish("请提供一个有效的位置")
        return
    if not (0 <= x < 4 and 0 <= y < 8):
        await _fanfan_fan_cmd.finish("坐标超出范围，请提供一个有效的位置")
        return
    result = game.fan(uid, x, y)
    if not result.startswith("翻开了"):
        await _fanfan_fan_cmd.finish(result)
        return
    result += f"\n轮到{at_user(game.current_player())}行动\n"
    result += "将＞士＞象＞马＞车＞炮＞兵，但兵能吃将，炮只能隔子吃（隔子吃无视大小）"
    result += "\n你可以输入：\n"
    result += f"- {input_link("翻开")} 行号 列号\n"
    result += f"- {input_link("移动")} 行号 列号 上/下/左/右\n"
    result += f"- {input_link("移动")} 行号 列号 到 行号 列号\n"
    result += "\n当前盘面：\n\n---\n\n" + game.display_board()
    result += game.check_game_over()
    await _fanfan_fan_cmd.finish(MessageSegment.markdown(result))


_fanfan_move_cmd = on_command("移动", priority=10, block=True)

_fanfan_move_format = "命令格式：\n/移动 起始行号 起始列号 上/下/左/右\n/移动 起始行号 起始列号 到 目标行号 目标列号"


@_fanfan_move_cmd.handle()
async def _handle_fanfan_move(event: Event, args=CommandArg()):
    uid = event.get_user_id()
    game = fanfan_games.get(uid)
    if game is None:
        await _fanfan_move_cmd.finish("你还没有开始游戏，请先使用命令：\n象棋翻翻棋 @对手")
        return
    if uid != game.current_player():
        await _fanfan_move_cmd.finish(f"现在轮到对方行动")
        return
    arr: str = args.extract_plain_text().strip().replace(" ", "")
    if len(arr) < 3:
        await _fanfan_move_cmd.finish(_fanfan_move_format)
        return
    try:
        x1 = int(arr[0]) - 1
        y1 = int(arr[1]) - 1
    except ValueError:
        await _fanfan_move_cmd.finish(_fanfan_move_format)
        return
    if arr[2] == "左":
        x2, y2 = x1, y1 - 1
    elif arr[2] == "右":
        x2, y2 = x1, y1 + 1
    elif arr[2] == "上":
        x2, y2 = x1 - 1, y1
    elif arr[2] == "下":
        x2, y2 = x1 + 1, y1
    elif len(arr) >= 5 and arr[2] == "到":
        try:
            x2 = int(arr[3]) - 1
            y2 = int(arr[4]) - 1
        except ValueError:
            await _fanfan_move_cmd.finish(_fanfan_move_format)
            return
    else:
        await _fanfan_move_cmd.finish(_fanfan_move_format)
        return
    if not (0 <= x1 < 4 and 0 <= y1 < 8 and 0 <= x2 < 4 and 0 <= y2 < 8):
        await _fanfan_move_cmd.finish("坐标超出范围，请提供有效的位置")
    result = game.move(uid, x1, y1, x2, y2)
    if "移动了" not in result:
        await _fanfan_move_cmd.finish(result)
    result += f"\n轮到{at_user(game.current_player())}行动\n"
    result += "将＞士＞象＞马＞车＞炮＞兵，但兵能吃将，炮只能隔子吃（隔子吃无视大小）"
    result += "\n你可以输入：\n"
    result += f"- {input_link("翻开")} 行号 列号\n"
    result += f"- {input_link("移动")} 行号 列号 上/下/左/右\n"
    result += f"- {input_link("移动")} 行号 列号 到 行号 列号\n"
    result += "\n当前盘面：\n\n---\n\n" + game.display_board()
    result += game.check_game_over()
    await _fanfan_move_cmd.finish(MessageSegment.markdown(result))


__fanfan_end_cmd = on_command("结束游戏", force_whitespace=True, priority=10, block=True)


@__fanfan_end_cmd.handle()
async def _handle_fanfan_end(event: Event):
    uid = event.get_user_id()
    game = fanfan_games.get(uid)
    if game is None:
        await __fanfan_end_cmd.finish("你还没有开始游戏，请先使用命令：\n象棋翻翻棋 @对手")
        return
    del fanfan_games[game.uid1]
    del fanfan_games[game.uid2]
    await __fanfan_end_cmd.finish("游戏已结束")