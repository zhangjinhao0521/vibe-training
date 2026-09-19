"""个人穿搭记账本：在终端记录每日穿搭并保存到本地。"""

from __future__ import annotations

import json
import os
import re
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


DATA_FILE = Path(
    os.environ.get("OUTFIT_DATA_FILE", Path(__file__).with_name("data.json"))
)


def backup_invalid_data(path: Path) -> Path | None:
    """在忽略异常数据前保留原文件，避免后续保存造成数据丢失。"""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = path.with_name(f"{path.stem}.invalid-{stamp}{path.suffix}")
    try:
        shutil.copy2(path, backup_path)
    except OSError:
        return None
    return backup_path


def is_valid_record(record: object) -> bool:
    if not isinstance(record, dict):
        return False
    try:
        date.fromisoformat(str(record.get("date", "")))
    except ValueError:
        return False

    required_text = ("top", "bottom", "shoes", "style", "occasion")
    if any(
        not isinstance(record.get(field), str) or not record[field].strip()
        for field in required_text
    ):
        return False
    colors = record.get("colors")
    if not isinstance(colors, list) or not colors:
        return False
    if any(not isinstance(color, str) or not color.strip() for color in colors):
        return False
    rating = record.get("rating")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        return False
    return isinstance(record.get("note", ""), str)


def load_records(path: Path = DATA_FILE) -> list[dict]:
    """读取已有穿搭记录；文件不存在时返回空列表。"""
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except OSError as error:
        print(f"读取数据失败：{error}。请检查文件权限后重试。")
        return []
    except json.JSONDecodeError as error:
        backup = backup_invalid_data(path)
        backup_message = f"，原文件已备份为 {backup.name}" if backup else ""
        print(f"数据文件不是有效的 JSON{backup_message}，本次从空记录开始。")
        return []

    if not isinstance(data, list):
        backup = backup_invalid_data(path)
        backup_message = f"，原文件已备份为 {backup.name}" if backup else ""
        print(f"数据文件格式不正确{backup_message}，本次从空记录开始。")
        return []

    valid_records = [record for record in data if is_valid_record(record)]
    invalid_count = len(data) - len(valid_records)
    if invalid_count:
        backup = backup_invalid_data(path)
        backup_message = f"，原文件已备份为 {backup.name}" if backup else ""
        print(f"已忽略 {invalid_count} 条格式异常的记录{backup_message}。")
    return valid_records


def save_records(records: list[dict], path: Path = DATA_FILE) -> None:
    """以 UTF-8 JSON 原子写入全部记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        temporary_path.replace(path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


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
        if field == "month":
            while True:
                value = prompt_required(prompt)
                if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
                    break
                print("月份格式不正确，请输入例如 2026-09。")
        else:
            value = prompt_required(prompt)
    matched = filter_records(records, field, value)
    print_records(matched)
    return matched


def prompt_month() -> str:
    current_month = date.today().strftime("%Y-%m")
    while True:
        value = input(
            f"要总结的月份（YYYY-MM，回车默认 {current_month}）："
        ).strip() or current_month
        if re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            return value
        print("月份格式不正确，请输入例如 2026-09。")


def next_month(month: str) -> str:
    year, month_number = (int(part) for part in month.split("-"))
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def ranked_items(counter: Counter, limit: int = 3) -> list[tuple[str, int]]:
    """按次数降序、名称升序返回稳定的排名。"""
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]


def build_monthly_summary(records: list[dict], month: str) -> dict | None:
    month_records = filter_records(records, "month", month)
    if not month_records:
        return None

    counters = {
        "style": Counter(str(record.get("style", "未记录")) for record in month_records),
        "color": Counter(
            str(color)
            for record in month_records
            for color in record.get("colors", [])
        ),
        "top": Counter(str(record.get("top", "未记录")) for record in month_records),
        "bottom": Counter(str(record.get("bottom", "未记录")) for record in month_records),
        "shoes": Counter(str(record.get("shoes", "未记录")) for record in month_records),
        "occasion": Counter(
            str(record.get("occasion", "未记录")) for record in month_records
        ),
    }
    ratings = [int(record.get("rating", 0)) for record in month_records]

    grouped: defaultdict[tuple, list[dict]] = defaultdict(list)
    for record in month_records:
        key = (
            str(record.get("top", "未记录")),
            str(record.get("bottom", "未记录")),
            str(record.get("shoes", "未记录")),
            tuple(str(color) for color in record.get("colors", [])),
            str(record.get("style", "未记录")),
            str(record.get("occasion", "未记录")),
        )
        grouped[key].append(record)

    recommendations = []
    for key, group in grouped.items():
        average = sum(int(record.get("rating", 0)) for record in group) / len(group)
        recommendations.append(
            {
                "top": key[0],
                "bottom": key[1],
                "shoes": key[2],
                "colors": list(key[3]),
                "style": key[4],
                "occasion": key[5],
                "average_rating": average,
                "count": len(group),
                "latest_date": max(str(record.get("date", "")) for record in group),
            }
        )
    recommendations.sort(
        key=lambda item: (
            -item["average_rating"],
            -item["count"],
            item["top"],
            item["bottom"],
            item["shoes"],
        )
    )

    return {
        "month": month,
        "next_month": next_month(month),
        "count": len(month_records),
        "average_rating": sum(ratings) / len(ratings),
        "counters": counters,
        "recommendations": recommendations[:3],
    }


def format_ranking(counter: Counter) -> str:
    ranked = ranked_items(counter)
    return "、".join(f"{name}（{count} 次）" for name, count in ranked) or "未记录"


def print_monthly_summary(summary: dict) -> None:
    print(f"\n--- {summary['month']} 月度穿搭总结 ---")
    print(f"记录次数：{summary['count']} 次")
    print(f"平均满意度：{summary['average_rating']:.1f}/5")
    labels = {
        "style": "常穿风格",
        "color": "常用颜色",
        "top": "常穿上装",
        "bottom": "常穿下装",
        "shoes": "常穿鞋履",
        "occasion": "常见场合",
    }
    for key, label in labels.items():
        print(f"{label}：{format_ranking(summary['counters'][key])}")

    print(f"\n--- {summary['next_month']} 穿搭推荐 ---")
    for index, item in enumerate(summary["recommendations"], start=1):
        colors = "、".join(item["colors"]) or "未记录"
        print(
            f"{index}. {item['top']} + {item['bottom']} + {item['shoes']} "
            f"| {colors} | {item['style']}"
        )
        print(
            f"   适合：{item['occasion']}；依据：本月穿过 {item['count']} 次，"
            f"平均满意度 {item['average_rating']:.1f}/5。"
        )


def show_monthly_summary(records: list[dict]) -> dict | None:
    print("\n--- 月度偏好总结与下月推荐 ---")
    month = prompt_month()
    summary = build_monthly_summary(records, month)
    if summary is None:
        print("该月暂无穿搭记录，暂时无法总结和推荐。")
        return None
    print_monthly_summary(summary)
    return summary


def delete_outfit(records: list[dict], path: Path = DATA_FILE) -> bool:
    print("\n--- 删除穿搭记录 ---")
    if not records:
        print("还没有穿搭记录，无需删除。")
        return False

    ordered_records = filter_records(records)
    print_records(ordered_records)
    while True:
        value = input("请输入要删除的编号（直接回车取消）：").strip()
        if not value:
            print("已取消删除。")
            return False
        try:
            selected = int(value)
        except ValueError:
            print("编号必须是整数，请重新输入。")
            continue
        if 1 <= selected <= len(ordered_records):
            break
        print(f"编号超出范围，请输入 1~{len(ordered_records)}。")

    target = ordered_records[selected - 1]
    print(
        f"将删除：{target.get('date', '日期未知')} | "
        f"{target.get('top', '未记录')} + {target.get('bottom', '未记录')} + "
        f"{target.get('shoes', '未记录')}"
    )
    while True:
        confirmation = input("确认删除？(y/n)：").strip().casefold()
        if confirmation in {"n", "no", "否", ""}:
            print("已取消删除，记录仍然保留。")
            return False
        if confirmation in {"y", "yes", "是"}:
            break
        print("请输入 y 或 n。")

    original_index = next(
        index for index, record in enumerate(records) if record is target
    )
    records.pop(original_index)
    save_records(records, path)
    print("记录已删除。")
    return True


def print_menu() -> None:
    print("\n=== 个人穿搭记账本 ===")
    print("1. 记录今日穿搭")
    print("2. 查看与筛选穿搭")
    print("3. 月度偏好总结与下月推荐")
    print("4. 删除穿搭记录")
    print("5. 退出")


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
            show_monthly_summary(records)
        elif choice == "4":
            delete_outfit(records)
        elif choice == "5":
            print("已退出，明天见。")
            return
        else:
            print("无效选项，请输入 1~5。")


if __name__ == "__main__":
    main()
