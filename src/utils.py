from datetime import datetime
import json
import logging
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Определяем корень проекта (папка, где лежит src/)
project_root: Path = Path(__file__).resolve().parent.parent

# Создаем директорию logs в корне проекта, если её нет
logs_dir: Path = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logger: logging.Logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)

# Файловый обработчик для логов
file_handler: logging.FileHandler = logging.FileHandler(logs_dir / "utils.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter: logging.Formatter = logging.Formatter("{asctime} - {name} - {levelname}: {message}", style="{")
file_handler.setFormatter(formatter)

# Подключаем обработчик
logger.addHandler(file_handler)


def determine_greeting(datetime_str):
    """
    Определяет приветствие в зависимости от времени суток.

    Args:
        datetime_str (str): Дата и время в формате DD-MM-YYYY HH:MM:SS

    Returns:
        str: Текст приветствия ('Доброе утро', 'Добрый день', ...)
    """
    dt = datetime.strptime(datetime_str, "%d-%m-%Y %H:%M:%S")
    hour = dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 24:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def calculate_card_data(start_date, end_date):
    """
    Вычисляет данные по картам за указанный период.

    Args:
        start_date: Начальная дата периода в формате DD-MM-YYYY
        end_date: Конечная дата периода в формате DD-MM-YYYY

    Returns:
        Список карточных данных
    """
    df = pd.read_excel("data/operations.xlsx")

    # Преобразуем даты в формат datetime с указанием формата DD-MM-YYYY
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format='%d.%m.%Y')

    # Фильтруем данные по дате
    mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
    filtered_df = df.loc[mask]

    # Группируем по номеру карты и суммируем операции
    grouped = filtered_df.groupby("Номер карты").agg({"Сумма операции": "sum"}).reset_index()

    # Рассчитываем кэшбэк (1% от суммы операций)
    grouped["cashback"] = grouped["Сумма операции"] * 0.01

    # Получаем последние 4 цифры номера карты
    grouped["last_digits"] = grouped["Номер карты"].astype(str).str[-4:]

    # Удаляем столбец с номером карты
    del grouped["Номер карты"]

    # Возвращаем результат в виде списка словарей
    return grouped.to_dict("records")


def retrieve_top_transactions(start_date, end_date):
    """
    Извлекает топ-5 транзакций за указанный период.

    Args:
        start_date (str): Начальная дата периода в формате DD-MM-YYYY
        end_date (str): Конечная дата периода в формате DD-MM-YYYY

    Returns:
        list of dicts: Список топ-транзакций
    """
    df = pd.read_excel("data/operations.xlsx")

    # Преобразуем даты в формат datetime с указанием формата DD-MM-YYYY
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format='%d.%m.%Y')

    # Фильтруем данные по дате
    mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
    filtered_df = df.loc[mask]

    # Сортируем по сумме операции и берем топ-5
    sorted_df = filtered_df.sort_values(by="Сумма операции", ascending=False).head(5)

    return sorted_df.to_dict("records")


def get_currency_rates() -> dict:
    """
    Получает актуальные курсы валют относительно российского рубля (RUB).

    Данная функция считывает API-ключ из переменной окружения CURRENCY_API_KEY,
    загружает необходимые настройки из файла user_settings.json, отправляет запрос
    к внешнему сервису exchangerates_data и возвращает нормализованный словарь
    с информацией о курсах выбранных валют.

    Returns:
        dict: Словарь с ключом 'currency_rates', содержащий список объектов вида:
              {'currency': str, 'rate': float}, где rate представляет собой обратное
              отношение курса выбранной валюты к рублю (округлено до 2-х десятичных знаков).

    Raises:
        EnvironmentError: Возникает, если переменная среды CURRENCY_API_KEY не определена.
        FileNotFoundError: Генерируется, когда файл user_settings.json отсутствует.
        json.JSONDecodeError: Исключение появляется при некорректном формате JSON в файле настроек.
        ValueError: Ошибка выдается, если в конфигурации отсутствуют нужные валюты.
        requests.RequestException: Любая ошибка, связанная с сетевым взаимодействием или обработкой ответа сервера.
    """
    # Загрузка переменных окружения
    load_dotenv()
    api_key: str | None = os.getenv("CURRENCY_API_KEY")
    if not api_key:
        raise EnvironmentError("Переменная CURRENCY_API_KEY не найдена!")

    # Чтение пользовательских настроек
    try:
        with open("user_settings.json", "r") as f:
            settings: dict = json.load(f)
    except FileNotFoundError:
        print("Файл user_settings.json не найден!")
        exit(1)
    except json.JSONDecodeError:
        print("Ошибка формата JSON в файле user_settings.json!")
        exit(1)

    # Проверка наличия нужных валют в настройках
    symbols: list[str] = settings.get("user_currencies", [])
    if not symbols:
        print("Нет валют в конфиг-файле!")
        exit(1)

    # Отправка запроса к API
    try:
        response = requests.get(
            "https://api.apilayer.com/exchangerates_data/latest",
            headers={"apikey": api_key},
            params={"base": "RUB", "symbols": ",".join(symbols)},
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Произошла ошибка при обращении к API: {e}")
        exit(1)

    # Обработка полученных данных
    data: dict = response.json()
    rates_data: dict = data["rates"]

    # Формирование результата
    rates = [{"currency": currency, "rate": round(1 / rates_data[currency], 2)} for currency in symbols]

    return {"currency_rates": rates}


def get_stock_prices() -> dict:
    """
    Получает актуальные цены акций, указанных в пользовательской конфигурации.

    Эта функция считывает API-ключ из переменной окружения STOCK_API_KEY,
    загружает необходимые настройки из файла user_settings.json, отправляет запрос
    к внешнему сервису Alpha Vantage и возвращает нормализованный словарь
    с информацией о ценах выбранных акций.

    Returns:
        dict: Словарь с ключом 'stock_prices', содержащий список объектов вида:
              {'stock': str, 'price': float}, где price округлен до двух десятичных знаков.

    Raises:
        EnvironmentError: Возникает, если переменная среды STOCK_API_KEY не определена.
        FileNotFoundError: Генерируется, когда файл user_settings.json отсутствует.
        json.JSONDecodeError: Исключение появляется при некорректном формате JSON в файле настроек.
        ValueError: Ошибка выдается, если в конфигурации отсутствуют символы акций.
        requests.RequestException: Любая ошибка, связанная с сетевым взаимодействием или обработкой ответа сервера.
    """
    # Загрузка переменных окружения
    load_dotenv()
    api_key = os.getenv("STOCK_API_KEY")
    if not api_key:
        raise EnvironmentError("Переменная STOCK_API_KEY не найдена!")

    # Чтение пользовательских настроек
    try:
        with open("user_settings.json", "r") as f:
            settings: dict = json.load(f)
    except FileNotFoundError:
        print("Файл user_settings.json не найден!")
        exit(1)
    except json.JSONDecodeError:
        print("Ошибка формата JSON в файле user_settings.json!")
        exit(1)

    # Проверка наличия нужных акций в настройках
    symbols: list[str] = settings.get("user_stocks", [])
    if not symbols:
        print("Нет символов акций в конфиг-файле!")
        exit(1)

    # Сбор данных о ценах акций
    prices = []
    for symbol in symbols:
        try:
            response = requests.get(
                f"https://www.alphavantage.co/query?"
                f"function=TIME_SERIES_INTRADAY&symbol={symbol}&"
                f"interval=1min&apikey={api_key}"
            )
            response.raise_for_status()

            data = response.json()
            latest_data = list(data["Time Series (1min)"].values())[0]
            price = float(latest_data["4. close"])
            prices.append({"stock": symbol, "price": round(price, 2)})
        except requests.RequestException as e:
            print(f"Ошибка при получении данных для {symbol}: {e}")
        except Exception as e:
            print(f"Непредвиденная ошибка при обработке данных для {symbol}: {e}")

    return {"stock_prices": prices}
