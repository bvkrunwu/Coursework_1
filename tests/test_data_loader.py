import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import load_operations_data

# Импортируем тестируемую функцию


# Фикстура для временного Excel-файла
@pytest.fixture
def excel_file():
    """Создает временный Excel-файл с образцом данных"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df = pd.DataFrame({
            'Дата операции': ['2023-01-01'],
            'Сумма операции': [100]
        })
        df.to_excel(f.name, index=False)
        yield f.name
    Path(f.name).unlink(missing_ok=True)

# Фикстура для временного CSV-файла (некорректный формат)
@pytest.fixture
def csv_file():
    """Создает временный CSV-файл для проверки некорректного формата"""
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'Дата операции': ['2023-01-01'],
            'Сумма операции': [100]
        })
        df.to_csv(f.name, index=False)
        yield f.name
    Path(f.name).unlink(missing_ok=True)

# Тест для стандартной успешной загрузки
def test_load_operations_success(excel_file):
    """Проверяет успешную загрузку данных из существующего Excel-файла"""
    df = load_operations_data(excel_file)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert set(df.columns) == {'Дата операции', 'Сумма операции'}

# Тест для обработки отсутствующего файла
def test_load_operations_file_not_found():
    """Проверяет реакцию на попытку загрузки несуществующего файла"""
    nonexistent_file = "nonexistent.xlsx"
    with pytest.raises(FileNotFoundError):
        load_operations_data(nonexistent_file)

# Тест для обработки некорректного формата файла
def test_load_operations_incorrect_format(csv_file):
    """Проверяет реакцию на попытку загрузки файла с некорректным форматом"""
    with pytest.raises(ValueError):
        load_operations_data(csv_file)