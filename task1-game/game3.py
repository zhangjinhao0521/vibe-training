import random
from datetime import datetime
from pathlib import Path


SCORES_FILE = Path(__file__).with_name("scores.txt")


def save_score(result, attempts):
    date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with SCORES_FILE.open("a", encoding="utf-8") as file:
        file.write(f"{date_time},{result},{attempts}\n")


def play_game():
    answer = random.randint(1, 100)
    attempts = 0
    print("我已经想好了一个 1 到 100 之间的整数。")

    while attempts < 7:
        text = input("请输入你的猜测：")
        try:
            guess = int(text)
        except ValueError:
            print("请输入 1~100 之间的整数")
            continue

        if not 1 <= guess <= 100:
            print("请输入 1~100 之间的整数")
            continue

        attempts += 1
        if guess < answer:
            print("小了！")
        elif guess > answer:
            print("大了！")
        else:
            print(f"猜对了！你一共猜了 {attempts} 次。")
            save_score("胜", attempts)
            return

    print(f"次数用完了，你输了！答案是 {answer}。")
    save_score("负", attempts)


def show_leaderboard():
    records = []
    if SCORES_FILE.exists():
        with SCORES_FILE.open("r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) != 3 or parts[1] != "胜":
                    continue
                try:
                    attempts = int(parts[2])
                except ValueError:
                    continue
                records.append((attempts, parts[0]))

    records.sort(key=lambda record: (record[0], record[1]))
    print("\n历史最少次数前 5 名（只统计获胜局）")
    if not records:
        print("暂无获胜记录。")
        return

    for rank, (attempts, date_time) in enumerate(records[:5], start=1):
        print(f"{rank}. {date_time} - 胜 - {attempts} 次")


def start_games():
    while True:
        play_game()
        again = input("是否再来一局？输入 y 重开，其他输入退出：")
        if again.strip().lower() != "y":
            print("游戏结束！")
            return


def main():
    while True:
        print("\n=== 猜数字游戏 ===")
        print("1. 开始游戏")
        print("2. 查看历史最少次数前 5 名")
        print("3. 退出")
        choice = input("请选择：").strip()

        if choice == "1":
            start_games()
            return
        if choice == "2":
            show_leaderboard()
        elif choice == "3":
            print("游戏结束！")
            return
        else:
            print("请输入 1、2 或 3。")


if __name__ == "__main__":
    main()
