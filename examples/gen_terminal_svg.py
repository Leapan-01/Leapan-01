# -*- coding: utf-8 -*-
"""生成「终端打字机」SVG。

How To Use(lll￢ω￢)：
    python gen_terminal_svg.py terminal.svg

  · cmd 行   —— 敲命令
  · out 行   —— 回显，
  · ls  行   —— 列表输出

自适应喵

每个字符是一个 <tspan>，自带 SMIL <animate> 控制 opacity；
不写 opacity 属性（基础值默认 1），所以碰上不支持 SMIL 的渲染器时，
会直接显示完整文本，而不是一片空白。
"""

import re
import sys
from xml.sax.saxutils import escape

# ---------- 链接（ls 段由这里生成，自动对齐） ----------
LINKS = [
    ("Blog", "https://blog.gardenwalk.moe"),
    ("HomePage", "https://www.gardenwalk.moe"),
    ("Twitter", "https://x.com/leapan_01"),
    ("bilibili", "https://space.bilibili.com/667164368"),
    ("Pixiv", "https://www.pixiv.net/users/116413297"),
    ("E-mail", "lp-gardenwalk@outlook.com"),
]


def ls_line(name, url):
    width = max(len(n) for n, _ in LINKS)
    return "lrwxr-xr-x  {:<{width}}  -> {}".format(name, url, width=width)


# ---------- 内容 ----------
LINES = [
    ("cmd", "$ whoami"),
    ("out", "Leapan"),
    ("blank", ""),
    ("cmd", "$ cat ~/about.txt"),
    ("out", "采菊东篱下，悠然见南山。"),
    ("out", "代码，摄影，银河，维护与卖萌。"),
    ("blank", ""),
    ("cmd", '$ echo "数字田园的悠然漫步"'),
    ("out", "数字田园的悠然漫步"),
    ("blank", ""),
    ("cmd", "$ ./life --mode=slow"),
    ("out", "Wandering, observing, creating."),
    ("blank", ""),
    ("cmd", "$ ls -l ~/links"),
] + [("ls", ls_line(name, url)) for name, url in LINKS] + [
    ("blank", ""),
    ("cmd", "$ exit"),
]

# ---------- 排版 ----------
FONT_SIZE = 14
LINE_HEIGHT = 22
PAD_LEFT = 24
PAD_RIGHT = 24
FIRST_BASELINE = 48
PAD_BOTTOM = 22

FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', monospace")


def text_width(text):
    total = 0.0
    for ch in text:
        total += 1.0 if ord(ch) > 0x2E80 else 0.6
    return total * FONT_SIZE


WIDTH = int(PAD_LEFT + PAD_RIGHT
            + max(text_width(t) for _k, t in LINES) + 24)
HEIGHT = FIRST_BASELINE + (len(LINES) - 1) * LINE_HEIGHT + PAD_BOTTOM

BG = "#161b22"
C_PROMPT = "#7ee787"   # $
C_CMD = "#e6edf3"      # 命令本体
C_OUT = "#a8b1bb"      # 普通输出
C_PERM = "#79c0ff"     # ls 的权限位
C_NAME = "#e6edf3"     # ls 的文件名
C_SYS = "#6e7681"      # 系统消息前缀

# ---------- 时间轴（秒） ----------
LEAD = 0.7
SPEED = {"cmd": 0.075, "out": 0.030, "ls": 0.012}
PAUSE = {"cmd": 0.22, "out": 0.14, "ls": 0.05, "blank": 0.12}
TAIL = 2.8


def colors_for(kind, text):
    """返回每个字符的颜色。"""
    if kind == "cmd":
        return [C_PROMPT if ch == "$" else C_CMD for ch in text]
    if kind == "out":
        if text.startswith("logout:"):
            return [C_SYS] * 7 + [C_OUT] * (len(text) - 7)
        return [C_OUT] * len(text)
    if kind == "ls":
        matched = re.match(r"^(l\S{9})(\s+)(\S+)(\s+->\s+)(.*)$", text)
        if not matched:
            return [C_OUT] * len(text)
        fills = []
        for idx, piece in enumerate(matched.groups()):
            if idx == 0:
                fills += [C_PERM] * len(piece)
            elif idx == 2:
                fills += [C_NAME] * len(piece)
            else:
                fills += [C_OUT] * len(piece)
        return fills
    return [C_OUT] * len(text)


def build_timeline():
    appear = {}
    t = LEAD
    for row, (kind, text) in enumerate(LINES):
        speed = SPEED.get(kind, 0.03)
        for col, _ch in enumerate(text):
            appear[(row, col)] = t
            t += speed
        t += PAUSE.get(kind, 0.12)
    return appear, t


def char_tspan(ch, fill, t_in, total):
    t1 = t_in / total
    t2 = min(t1 + 0.002, 0.99)
    key_times = "0;{:.5f};{:.5f};0.995;1".format(t1, t2)
    anim = ("<animate attributeName='opacity' dur='{:.2f}s' "
            "repeatCount='indefinite' values='0;0;1;1;0' "
            "keyTimes='{}'/>").format(total, key_times)
    return "<tspan fill='{}'>{}{}</tspan>".format(fill, anim, escape(ch))


def main(out_path):
    appear, typing_end = build_timeline()
    total = typing_end + TAIL

    parts = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='{}' height='{}' "
        "viewBox='0 0 {} {}' role='img' "
        "aria-label='终端会话：whoami、about.txt、数字田园的悠然漫步、"
        "life --mode=slow、links 符号链接与 exit'>".format(
            WIDTH, HEIGHT, WIDTH, HEIGHT),
        "<rect width='{}' height='{}' rx='10' fill='{}'/>".format(
            WIDTH, HEIGHT, BG),
    ]

    for row, (kind, text) in enumerate(LINES):
        if not text:
            continue
        y = FIRST_BASELINE + row * LINE_HEIGHT
        fills = colors_for(kind, text)
        # tspan 之间绝对不能有换行或空格qwq，否则会被当成真实的空白字符，
        # 渲染出来就变成"每个字之间都空一格"。
        tspans = "".join(
            char_tspan(ch, fills[col], appear[(row, col)], total)
            for col, ch in enumerate(text)
        )
        parts.append(
            "<text x='{}' y='{}' font-family=\"{}\" font-size='{}' "
            "xml:space='preserve'>{}</text>".format(
                PAD_LEFT, y, FONT, FONT_SIZE, tspans))

    # 光标：闪
    last_row = len(LINES) - 1
    last_text = LINES[last_row][1]
    last_t = appear[(last_row, len(last_text) - 1)]
    cur_x = PAD_LEFT + text_width(last_text) + 3
    cur_y = FIRST_BASELINE + last_row * LINE_HEIGHT - 13
    t1 = last_t / total
    t2 = min(t1 + 0.002, 0.99)
    parts.append(
        "<g><animate attributeName='opacity' dur='{:.2f}s' "
        "repeatCount='indefinite' values='0;0;1;1;0' "
        "keyTimes='0;{:.5f};{:.5f};0.995;1'/>"
        "<rect x='{:.0f}' y='{}' width='8' height='16' fill='{}'>"
        "<animate attributeName='opacity' values='1;0' dur='0.85s' "
        "repeatCount='indefinite'/></rect></g>".format(
            total, t1, t2, cur_x, cur_y, C_PROMPT))

    parts.append("</svg>")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))

    print("写出 {}".format(out_path))
    print("  画布 {}x{}  行 {}  字符 {}".format(
        WIDTH, HEIGHT, len(LINES), len(appear)))
    print("  打字结束 {:.2f}s  循环 {:.2f}s".format(typing_end, total))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "terminal.svg")
