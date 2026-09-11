"""个人穿搭记账本：在终端记录每日穿搭并保存到本地。"""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path


DATA_FILE = Path(
    os.environ.get("OUTFIT_DATA_FILE", Path(__file__).with_name("data.json"))
)


def load_records(path: Path = DATA_FILE) -> list[dict]:
    """读取已有穿搭记录；文件不存在时返回空列表。"""
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"读取数据失败：{error}。本次将从空记录开始。")
        return []

    if not isinstance(data, list):
        print("数据文件格式不正确，本次将从空记录开始。")
        return []
    return data


def save_records(records: list[dict], path: Path = DATA_FILE) -> None:
    """以 UTF-8 JSON 格式保存全部记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def prompt_required(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("这一项不能为空，请重新输入。")


def prompt_date() -> str:
    today = date.today().isoformat()
    while True:
        value = input(f"穿搭日期（YYYY-MM-DD，回车默认 {today}）：").strip() or today
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            print("日期格式不正确，请输入例如 2026-09-11。")


def prompt_rating() -> int:
    while True:
        value = input("满意度（1~5）：").strip()
        try:
            rating = int(value)
        except ValueError:
            print("满意度必须是 1~5 的整数。")
            continue
        if 1 <= rating <= 5:
            return rating
        print("满意度必须在 1~5 之间。")


def split_terms(value: str) -> list[str]:
    """支持用中文或英文逗号输入多个颜色。"""
    normalized = value.replace("，", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def add_outfit(records: list[dict], path: Path = DATA_FILE) -> dict:
    print("\n--- 记录今日穿搭 ---")
    outfit = {
        "date": prompt_date(),
        "top": prompt_required("上装："),
        "bottom": prompt_required("下装："),
        "shoes": prompt_required("鞋履："),
        "colors": split_terms(prompt_required("主要颜色（多个可用逗号分隔）：")),
        "style": input("风格（回车默认 日常）：").strip() or "日常",
        "occasion": input("场合（回车默认 日常）：").strip() or "日常",
        "rating": prompt_rating(),
        "note": input("备注（可留空）：").strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    records.append(outfit)
    save_records(records, path)
    print("穿搭已保存。")
    return outfit


def filter_records(records: list[dict], field: str = "", value: str = "") -> list[dict]:
    """按月份、风格、颜色或场合筛选，并按日期倒序返回。"""
    query = value.strip().casefold()

    def matches(record: dict) -> bool:
        if not field or not query:
            return True
        if field == "month":
            return str(record.get("date", "")).startswith(query)
        if field == "color":
            colors = record.get("colors", [])
            return any(query in str(color).casefold() for color in colors)
        return query in str(record.get(field, "")).casefold()

    matched = [record for record in records if matches(record)]
    return sorted(
        matched,
        key=lambda record: (
            str(record.get("date", "")),
            str(record.get("created_at", "")),
        ),
        reverse=True,
    )


def print_records(records: list[dict]) -> None:
    if not records:
        print("没有符合条件的穿搭记录。")
        return

    print(f"\n共 {len(records)} 条穿搭记录：")
    for index, record in enumerate(records, start=1):
        colors = "、".join(record.get("colors", [])) or "未记录"
        note = record.get("note") or "无"
        print(
            f"\n[{index}] {record.get('date', '日期未知')} | "
            f"{record.get('style', '风格未知')} | "
            f"{record.get('occasion', '场合未知')} | "
            f"满意度 {record.get('rating', '?')}/5"
        )
        print(
            f"    上装：{record.get('top', '未记录')}；"
            f"下装：{record.get('bottom', '未记录')}；"
            f"鞋履：{record.get('shoes', '未记录')}"
        )
        print(f"    配色：{colors}；备注：{note}")


def view_outfits(records: list[dict]) -> list[dict]:
    print("\n--- 查看穿搭 ---")
    if not records:
        print("还没有穿搭记录，先去记录一套吧。")
        return []

    options = {
        "1": ("", ""),
        "2": ("month", "月份（YYYY-MM）："),
        "3": ("style", "风格关键词："),
        "4": ("color", "颜色关键词："),
        "5": ("occasion", "场合关键词："),
    }
    print("1. 查看全部  2. 按月份  3. 按风格  4. 按颜色  5. 按场合")
    while True:
        choice = input("筛选方式（回车默认查看全部）：").strip() or "1"
        if choice in options:
            break
        print("无效选项，请输入 1~5。")

    field, prompt = options[choice]
    value = ""
    if field:
        value = prompt_required(prompt)
    matched = filter_records(records, field, value)
    print_records(matched)
    return matched


def print_menu() -> None:
    print("\n=== 个人穿搭记账本 ===")
    print("1. 记录今日穿搭")
    print("2. 查看与筛选穿搭")
    print("3. 退出")


def main() -> None:
    records = load_records()
    while True:
        print_menu()
        choice = input("请选择：").strip()
        if choice == "1":
            add_outfit(records)
        elif choice == "2":
            view_outfits(records)
        elif choice == "3":
            print("已退出，明天见。")
            return
        else:
            print("无效选项，请输入 1、2 或 3。")


if __name__ == "__main__":
    main()
