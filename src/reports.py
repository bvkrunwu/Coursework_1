import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

# Определяем корень проекта (папка, где лежит src/)
project_root: Path = Path(__file__).resolve().parent.parent

# Создаем директорию reports в корне проекта, если её нет
reports_dir: Path = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

# Создаем директорию logs в корне проекта, если её нет
logs_dir: Path = project_root / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

# Настройка логирования
logger: logging.Logger = logging.getLogger("reports")
logger.setLevel(logging.DEBUG)

# Файловый обработчик для логов
file_handler: logging.FileHandler = logging.FileHandler(logs_dir / "reports.log", mode="w", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Форматирование логов
formatter: logging.Formatter = logging.Formatter("{asctime} - {name} - {levelname}: {message}", style="{")
file_handler.setFormatter(formatter)

# Подключаем обработчик
logger.addHandler(file_handler)


def report_writer(filename: Optional[str] = None) -> Callable[[Any], Any]:
    """
    Декоратор для записи результатов функций-отчётов в файл.
    """

    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result: pd.DataFrame = func(*args, **kwargs)

            # Генерируем имя файла по умолчанию, если не передано
            if filename is None:
                default_filename: str = f"{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                output_file_default: Path = reports_dir / default_filename
            else:
                output_file_custom: Path = reports_dir / filename

            output_file: Path = output_file_default if filename is None else output_file_custom

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result.to_dict("records"), f, ensure_ascii=False, indent=4)

            logger.info(f"Сохранён отчёт '{func.__name__}' в файл: {output_file}")
            return result

        return wrapper

    return decorator


@report_writer()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Формирует отчёт о тратах по заданной категории за последние три месяца.

    Аргументы:
        transactions (pd.DataFrame): датафрейм с транзакциями
        category (str): категория расходов
        date (Optional[str]): дата в формате ДД.ММ.ГГГГ (по умолчанию текущая дата)

    Возвращает:
        pd.DataFrame: таблица с суммами трат по месяцам
    """

    # Устанавливаем текущую дату, если не указана
    if date is None:
        current_date_current: datetime = datetime.today()
    else:
        current_date_specified: datetime = datetime.strptime(date, "%d.%m.%Y")

    current_date: datetime = current_date_current if date is None else current_date_specified

    # Вычисляем начальную дату трёхмесячного периода
    start_date: datetime = current_date - timedelta(days=90)

    # Конвертируем строку даты в объект datetime
    transactions["Дата платежа"] = pd.to_datetime(transactions["Дата платежа"], format="%d.%m.%Y")

    # Фильтруем транзакции по категории и периоду
    filtered_df: pd.DataFrame = transactions[
        (transactions["Категория"] == category)
        & (transactions["Дата платежа"] >= start_date)
        & (transactions["Дата платежа"] <= current_date)
    ]

    # Группируем суммы по месяцам
    grouped_df: pd.DataFrame = (
        filtered_df.groupby(filtered_df["Дата платежа"].dt.strftime("%B %Y"))["Сумма платежа"].sum().reset_index()
    )

    logger.info(f"Сформирован отчёт о тратах по категории '{category}' за последние три месяца.")

    return grouped_df


def load_transactions_from_excel(file_path: Optional[Union[Path, str]] = None) -> pd.DataFrame:
    """
    Загружает транзакции из Excel-файла в DataFrame.

    Если путь не указан, ищет файл data/operations.xlsx в корне проекта.

    Аргументы:
        file_path (Optional[Union[Path, str]]): путь к файлу Excel (относительный или абсолютный).
            Если None — используется стандартный путь: <корень_проекта>/data/operations.xlsx

    Возвращает:
        pd.DataFrame с данными транзакций

    Исключения:
        FileNotFoundError: если файл не найден
        Exception: если ошибка при чтении Excel
    """
    try:
        # Если путь не передан — формируем стандартный путь
        if file_path is None:
            file_path_standard: Path = project_root / "data" / "operations.xlsx"
            logger.info(f"Путь к файлу не указан. Используется стандартный путь: {file_path_standard}")
        elif isinstance(file_path, str):
            file_path_converted: Path = Path(file_path)

        file_path_used: Path = file_path_standard if file_path is None else file_path_converted

        # Проверяем существование файла
        if not file_path_used.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path_used}")

        # Читаем Excel
        df: pd.DataFrame = pd.read_excel(file_path_used)
        logger.info(f"Данные загружены из {file_path_used}. Найдено строк: {len(df)}")

        return df

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при чтении Excel-файла {file_path_used}: {e}")
        raise
