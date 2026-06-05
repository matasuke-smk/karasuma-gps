#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京都市営地下鉄 烏丸線の公式CSV(source/) から timetable.json を生成する。
（GPS版／出発駅・到着駅とも自由選択: 列車ごとに全停車駅の時刻を保持する）

south = 竹田方面(下り) / north = 国際会館方面(上り)
各列車 = {"dest": 行先(終着), "t": {駅名: "HH:MM", ...}}
アプリ側で出発駅・到着駅の時刻を引いて発着・所要を計算する。
"""
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
OUT = ROOT / "timetable.json"

ORDER = ["国際会館", "松ヶ崎", "北山", "北大路", "鞍馬口", "今出川", "丸太町",
         "烏丸御池", "四条", "五条", "京都", "九条", "十条", "くいな橋", "竹田"]

COORDS = {
    "国際会館": [35.062921, 135.785117], "松ヶ崎": [35.051652, 135.776071],
    "北山": [35.051243, 135.765209], "北大路": [35.044573, 135.758709],
    "鞍馬口": [35.037182, 135.759303], "今出川": [35.029394, 135.759369],
    "丸太町": [35.016288, 135.759553], "烏丸御池": [35.009974, 135.759619],
    "四条": [35.002518, 135.759588], "五条": [34.99494, 135.759714],
    "京都": [34.986192, 135.759968], "九条": [34.979177, 135.759668],
    "十条": [34.972577, 135.759716], "くいな橋": [34.962281, 135.757046],
    "竹田": [34.956439, 135.756124],
}

FILES = {
    "weekday": {"down": "烏丸線　平日　下り（竹田／新田辺・近鉄奈良方面）.csv",
                "up":   "烏丸線　平日　上り（国際会館方面）.csv"},
    "holiday": {"down": "烏丸線　土曜・休日　下り（竹田／新田辺・近鉄奈良方面）.csv",
                "up":   "烏丸線　土曜・休日　上り（国際会館方面）.csv"},
}


def load(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp932", "utf-8"):
        try:
            return list(csv.reader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"decode failed: {path}")


def trains(rows):
    """各列車について {dest, t:{駅:時刻}} を作る（烏丸線15駅ぶんのみ）。"""
    header = rows[3]
    idx = {st: header.index(st) for st in ORDER}
    out = []
    for r in rows[4:]:
        t = {}
        for st, ci in idx.items():
            if ci < len(r) and r[ci].strip():
                t[st] = r[ci].strip()
        if len(t) >= 2:
            out.append({"dest": (r[0] or "").strip(), "t": t})
    return out


def main():
    data = {
        "line": "烏丸線",
        "revision": "2025-02-22",
        "source": "出典: 京都市オープンデータ「京都市営地下鉄時刻表（令和7年2月22日改正）」CC BY 4.0"
                  "／近鉄直通ダイヤは令和8年3月14日改正",
        "note": "south=竹田方面/north=国際会館方面。方向は出発駅と到着駅の位置から自動判定。"
                "0:xxは翌日早朝。",
        "order": ORDER,
        "coords": COORDS,
    }
    for day, fs in FILES.items():
        data[day] = {
            "south": trains(load(SRC / fs["down"])),
            "north": trains(load(SRC / fs["up"])),
        }
        print(f"{day}: south {len(data[day]['south'])}本 / north {len(data[day]['north'])}本")

    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"-> {OUT}  ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
