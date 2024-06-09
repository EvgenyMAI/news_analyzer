import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

# Функция для извлечения среднего изменения из файла
def calculate_average_change(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                average_change = float(lines[0].strip().replace('%', ''))
                spread = float(lines[1].strip().replace('%', ''))
                return average_change, spread
    except FileNotFoundError:
        return 0.0, 0.0
    except ValueError:
        return 0.0, 0.0
    return 0.0, 0.0

def main():
    # Создание главного окна с темой 'flatly'
    root = tb.Window(themename="flatly")
    root.title("Обзор акций")
    root.geometry("1000x500")
    root.resizable(False, False)

    # Устанавливаем красивый шрифт
    default_font = ("Helvetica", 14)
    root.option_add("*Font", default_font)

    # Добавление заголовка
    label_text = "ОБЗОР АКЦИЙ"
    label = ttk.Label(root, text=label_text, font=("Helvetica", 24, "bold"), foreground="#ffffff", background="#2c3e50")
    label.pack(pady=20)

    label_text2 = "Найдите подробную информацию и инсайты о ваших любимых акциях."
    label2 = ttk.Label(root, text=label_text2, font=("Helvetica", 14), foreground="#ffffff", background="#2c3e50")
    label2.pack()

    # Создание таблицы
    columns = ("Название акции", "Текущая цена", "Предполагаемые изменения", "Разброс")
    tree = ttk.Treeview(root, columns=columns, show='headings', height=10)
    tree.heading("Название акции", text="Название акции")
    tree.heading("Текущая цена", text="Текущая цена")
    tree.heading("Предполагаемые изменения", text="Предполагаемые изменения")
    tree.heading("Разброс", text="Разброс")
    tree.column("Название акции", anchor='center', width=200)
    tree.column("Текущая цена", anchor='center', width=200)
    tree.column("Предполагаемые изменения", anchor='center', width=315)
    tree.column("Разброс", anchor='center', width=200)

    # Применение стилей к таблице
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 16, "bold"))
    style.configure("Treeview", font=("Helvetica", 14), rowheight=30)

    # Отображение таблицы
    tree.pack(pady=20)

    # Заполнение таблицы данными
    stocks = [
        ("Газпром", 122.78),
        ("Магнит", 6744),
        ("Металлоинвест", 867.2),
        ("МТС", 295.90),
        ("Тинькофф", 2957),
    ]

    for stock_name, current_price in stocks:
        filename = f'output/output_{stock_name.replace(" ", "_")}.txt'
        average_change, spread = calculate_average_change(filename)

        # Рассчитываем итоговую предполагаемую цену
        predicted_price = current_price + (current_price * average_change / 100)

        # Вычисляем изменения в рублях
        change_rub = current_price * average_change / 100
        spread_rub = current_price * spread / 100

        # Форматируем строки с изменениями
        change_str = f"{change_rub:.2f} ₽"
        predicted_price_str = f"{predicted_price:.2f} ₽ ± {spread_rub:.2f} ₽"

        # Добавляем данные в таблицу
        tree.insert("", "end", values=(stock_name, f"{current_price} ₽", change_str, predicted_price_str))

    # Установка фона окна
    root.configure(bg="#2c3e50")

    root.mainloop()

if __name__ == "__main__":
    main()
