import random


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
            return

    print(f"次数用完了，你输了！答案是 {answer}。")


def main():
    while True:
        play_game()
        again = input("是否再来一局？输入 y 重开，其他输入退出：")
        if again.strip().lower() != "y":
            print("游戏结束！")
            break


if __name__ == "__main__":
    main()
