import random


def main():
    answer = random.randint(1, 100)
    attempts = 0
    print("我已经想好了一个 1 到 100 之间的整数。")

    while True:
        text = input("请输入你的猜测：")
        try:
            guess = int(text)
        except ValueError:
            print("请输入整数，不能输入字母。")
            continue

        attempts += 1
        if guess < answer:
            print("小了！")
        elif guess > answer:
            print("大了！")
        else:
            print(f"猜对了！你一共猜了 {attempts} 次。")
            break


if __name__ == "__main__":
    main()
