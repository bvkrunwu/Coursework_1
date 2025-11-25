import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Определяем корень проекта (папка, где лежит src/)
project_root: Path = Path(__file__).resolve().parent.parent

# Создаем директорию logs в корне проекта, если её нет
logs_dir: Path = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logger: logging.Logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)

# Файловый обработчик для логов
file_handler: logging.FileHandler = logging.FileHandler(logs_dir / "services.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter: logging.Formatter = logging.Formatter("{asctime} - {name} - {levelname}: {message}", style="{")
file_handler.setFormatter(formatter)

# Подключаем обработчик
logger.addHandler(file_handler)


def analyze_cashback_categories(data: List[Dict[str, Any]], year: int, month: int) -> str:
    """
    Функция для анализа выгодности категорий повышенного кешбэка.

    Args:
        data (List[Dict[str, Any]]): Список транзакций в формате словарей
        year (int): Год для анализа
        month (int): Месяц для анализа

     Returns:
        str: JSON-строка с суммой потенциального кешбэка по категориям
    """
    try:
        logger.info(f"Приступаем к анализу данных за {year}-{month}")

        # Фильтруем транзакции по месяцу и году
        filtered_transactions: List[Dict[str, Any]] = [
            transaction
            for transaction in data
            if (
                datetime.strptime(transaction["date"], "%Y-%m-%d").year == year
                and datetime.strptime(transaction["date"], "%Y-%m-%d").month == month
            )
        ]

        if not filtered_transactions:
            return "{}"

        logger.info("Отфильтрованные транзакции получены успешно")

        # Группируем транзакции по категориям и считаем сумму расходов
        category_sums: Dict[str, float] = {}
        for transaction in filtered_transactions:
            try:
                category: str = transaction["category"]
                amount: float = float(transaction["amount"])
                if category in category_sums:
                    category_sums[category] += amount
                else:
                    category_sums[category] = amount
            except KeyError:
                logger.warning(
                    f"Транзакция не содержит обязательных полей 'category' или 'amount': {transaction}. Пропущена."
                )
            except ValueError:
                logger.warning(
                    f"Некорректный формат значения 'amount': {transaction['amount']}. Пропущена транзакция."
                )

        logger.info("Суммы по категориям рассчитаны")

        # Формируем итоговый словарь с суммами кешбэка (предположительно 5% кешбэк)
        cashback_result: Dict[str, float] = {k: round(v * 0.05, 2) for k, v in category_sums.items()}

        logger.info(f"Сформировано {len(cashback_result)} категорий с результатами кешбэка.")

        # Конвертируем в JSON-строку
        result_json: str = json.dumps(cashback_result, ensure_ascii=False, indent=4)

        return result_json

    except Exception as e:
        logger.error(f"Возникла непредвиденная ошибка: {e}")
        return "{}"
