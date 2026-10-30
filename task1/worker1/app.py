import os
import shutil
import sys

DATA_DIR = "/var/data"
RESULT_DIR = "/var/result"
OUTPUT_FILE = os.path.join(RESULT_DIR, "data.txt")

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Каталог {DATA_DIR} не найден.")
        sys.exit(1)

    files = [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if os.path.isfile(os.path.join(DATA_DIR, f))
    ]

    if not files:
        print("В каталоге /var/data нет файлов.")
        sys.exit(1)

    # Поиск самого большого по объему файла
    largest_file = max(files, key=os.path.getsize)
    os.makedirs(RESULT_DIR, exist_ok=True)
    shutil.copyfile(largest_file, OUTPUT_FILE)
    print(f"Worker 1: Самый большой файл '{os.path.basename(largest_file)}' скопирован в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
