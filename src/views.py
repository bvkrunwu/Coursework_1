from datetime import datetime
from typing import Any, Dict

from src.utils import (calculate_card_data, determine_greeting, get_currency_rates, get_stock_prices,
                       retrieve_top_transactions)


def generate_home_response(date_time_str: str) -> Dict[str, Any]:
    """
    Генерирует JSON-ответ для главной страницы.

    Args:
        date_time_str (str): Входная дата-время в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        Dict[str, Any]: Словарь с JSON-структурой согласно ТЗ
    """
    # Парсим входную дату-время
    input_dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

    # Определяем начало месяца и саму дату
    start_date = input_dt.replace(day=1).strftime("%Y-%m-%d")
    end_date = input_dt.strftime("%Y-%m-%d")

    # Формируем приветственное сообщение на основе текущего времени
    greeting = determine_greeting(input_dt.strftime("%d-%m-%Y %H:%M:%S"))

    # Расчет сводных данных по карточкам за указанный период
    cards = calculate_card_data(start_date, end_date)

    # Выборка наиболее значимых транзакций за выбранный временной диапазон
    top_transactions = retrieve_top_transactions(start_date, end_date)

    # Получение актуальных курсов валют
    currency_rates = get_currency_rates()

    # Запрос котировок акций
    stock_prices = get_stock_prices()

    # Создание финального JSON-ответа
    response = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return response
