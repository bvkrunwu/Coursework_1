import pandas as pd


def load_operations_data(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """
    Загружает данные операций из Excel-файла.

    Эта функция считывает данные из указанного Excel-файла и возвращает их в виде таблицы DataFrame.
    Предполагаются операции финансового характера или аналогичные транзакционные данные.

    Args:
        file_path (str): Путь к файлу Excel, содержащему данные операций.
        По умолчанию используется файл "data/operations.xlsx".

    Returns:
        pd.DataFrame: Таблица данных, загруженная из Excel-файла.
    """
    return pd.read_excel(file_path)
