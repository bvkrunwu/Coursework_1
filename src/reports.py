import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

# Определяем корень проекта (папка, где лежит src/)
project_root: Path = Path(__file__).resolve().parent.parent

# Создаем директории reports и logs в корне проекта, если их нет
reports_dir: Path = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

logs_dir: Path = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logger: logging.Logger = logging.getLogger("reports")
logger.setLevel(logging.DEBUG)

# Файловый обработчик для логов
file_handler: logging.FileHandler = logging.FileHandler(
    logs_dir / "reports.log",
    mode="w",
    encoding="utf-8"
)
file_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter: logging.Formatter = logging.Formatter(
    "{asctime} - {name} - {levelname}: {message}",
    style="{"
)
file_handler.setFormatter(formatter)

# Подключаем обработчик
logger.addHandler(file_handler)


def report_writer(filename: Optional[str] = None) -> Callable[[Any], Any]:
    """
    Декоратор для записи результатов функций-отчетов в файл.

    Параметры:
        filename (Optional[str]): Имя файла для сохранения отчета.
                                 Если не указан, создается файл с именем вида `{функция_отчета}_YYYYMMDD_HHMMSS.json`.

    Возвращаемое значение:
        Callable[[Any], Any]: Обернутая функция-декоратор.
    """
    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result: pd.DataFrame = func(*args, **kwargs)

            # Генерируем имя файла по умолчанию, если не передано
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = reports_dir / f"{func.__name__}_{timestamp}.json"
            else:
                output_file = reports_dir / filename

            # Сохраняем результат в JSON-файл
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict('records'), f, ensure_ascii=False, indent=4)

            logger.info(f"Сохранён отчет '{func.__name__}' в файл: {output_file}")
            return result

        return wrapper

    return decorator


@report_writer()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> pd.DataFrame:
    """
    Формирует отчет о тратах по заданной категории за последние три месяца.

    Параметры:
        transactions (pd.DataFrame): Датафрейм с транзакциями.
        category (str): Категория расходов.
        date (Optional[str]): Дата в формате ДД.ММ.ГГГГ (по умолчанию текущая дата).
                             Отсчет трехмесячного периода ведется от этой даты.

    Возвращаемое значение:
        pd.DataFrame: Таблица с суммами трат по месяцам.
    """
    # Устанавливаем текущую дату, если не указана
    if date is None:
        current_date = datetime.today()
    else:
        current_date = datetime.strptime(date, "%d.%m.%Y")

    # Вычисляем начальную дату трехмесячного периода
    start_date = current_date - timedelta(days=90)

    # Преобразуем столбец даты в объект datetime
    transactions['Дата платежа'] = pd.to_datetime(
        transactions['Дата платежа'],
        format='%d.%m.%Y'
    )

    # Фильтруем транзакции по категории и периоду
    filtered_df = transactions[
        (transactions['Категория'] == category) &
        (transactions['Дата платежа'] >= start_date) &
        (transactions['Дата платежа'] <= current_date)
    ]

    # Группируем суммы по месяцам
    grouped_df = (
        filtered_df.groupby(filtered_df["Дата платежа"].dt.strftime("%B %Y"))["Сумма платежа"]
        .sum()
        .reset_index()
        .sort_values(by=["Дата платежа"])  # Явная сортировка по дате
    )

    logger.info(f"Сформирован отчет о тратах по категории '{category}' за последние три месяца.")

    return grouped_df
