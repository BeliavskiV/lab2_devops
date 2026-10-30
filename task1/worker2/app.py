import os
import sys

INPUT_FILE = "/var/data/data.txt"
RESULT_DIR = "/var/result"
OUTPUT_FILE = os.path.join(RESULT_DIR, "result.txt")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Файл {INPUT_FILE} не найден.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        # Извлекаем все целые числа из файла (учитывая пробелы и переносы строк)
        numbers = [int(token) for token in f.read().split()]

    if not numbers:
        print("Файл пуст или не содержит чисел.")
        sys.exit(1)

    product = numbers[0] * numbers[-1]

    os.makedirs(RESULT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"{product}\n")

    # Вывод результата на экран согласно условию
    print(f"Первое число: {numbers[0]}, Последнее число: {numbers[-1]}")
    print(f"Результат (произведение): {product}")

if __name__ == "__main__":
    main()
