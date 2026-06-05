#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
京都市営地下鉄 烏丸線の公式CSV(source/) から、全15駅・両方向の timetable.json を生成する。
（GPS版: 最寄り駅を出発駅にするため、各駅の発車時刻＋駅座標を持つ）

south = 竹田方面(下り)  … 各駅発 → 竹田 着
north = 国際会館方面(上り) … 各駅発 → 国際会館 着
"""
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
OUT = ROOT / "timetable.json"

# 路線順（北→南）
ORDER = ["国際会館", "松ヶ崎", "北山", "北大路", "鞍馬口", "今出川", "丸太町",
         "烏丸御池", "四条", "五条", "京都", "九条", "十条", "くいな橋", "竹田"]

# 駅座標（OpenStreetMap / Overpass より）
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


def per_station(rows, stations, arr_station):
    """stations の各駅について [行先, 発, 着(arr_station)] のリストを作る。"""
    header = rows[3]
    ai = header.index(arr_station)
    out = {}
    for st in stations:
        ci = header.index(st)
        trips = []
        for r in rows[4:]:
            if len(r) <= max(ci, ai):
                continue
            dep, arr = r[ci].strip(), r[ai].strip()
            if not dep or not arr:
                continue
            trips.append([(r[0] or "").strip(), dep, arr])
        out[st] = trips
    return out


def main():
    data = {
        "line": "烏丸線",
        "revision": "2025-02-22",
        "source": "出典: 京都市オープンデータ「京都市営地下鉄時刻表（令和7年2月22日改正）」CC BY 4.0"
                  "／近鉄直通ダイヤは令和8年3月14日改正",
        "note": "south=竹田方面/north=国際会館方面。着時刻は終点(竹田・国際会館)着。0:xxは翌日早朝。",
        "order": ORDER,
        "coords": COORDS,
    }
    south_st = ORDER[:-1]   # 国際会館..くいな橋 (竹田始発の南行きは扱わない)
    north_st = ORDER[1:]    # 松ヶ崎..竹田       (国際会館始発の北行きは扱わない)
    for day, fs in FILES.items():
        down, up = load(SRC / fs["down"]), load(SRC / fs["up"])
        data[day] = {
            "south": per_station(down, south_st, "竹田"),
            "north": per_station(up, north_st, "国際会館"),
        }
        sc = sum(len(v) for v in data[day]["south"].values())
        nc = sum(len(v) for v in data[day]["north"].values())
        print(f"{day}: south {sc}本 ({len(south_st)}駅) / north {nc}本 ({len(north_st)}駅)")

    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"-> {OUT}  ({OUT.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
