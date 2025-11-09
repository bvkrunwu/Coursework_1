from datetime import datetime
from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

from src.reports import load_transactions_from_excel, report_writer, spending_by_category

# --- Фикстуры ---

@pytest.fixture(scope="session")
def sample_excel_file(tmpdir_factory):
    tmp_dir = tmpdir_factory.mktemp("data")
    excel_file = tmp_dir.join("sample.xlsx")
    # Создаём тестовый DataFrame с 10-ю строками
    df = pd.DataFrame({
        "Дата платежа": ["01.12.2018"]*10,
        "Категория": ["Супермаркет"]*10,
        "Сумма платежа": list(range(-1000, -990)),
    })
    # Сохраняем DataFrame в XLSX-файл
    df.to_excel(str(excel_file), index=False)
    return str(excel_file)

@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        "Дата платежа": ["01.12.2018", "15.11.2018"],
        "Категория": ["Супермаркет", "Транспорт"],
        "Сумма платежа": [-1000, -500],
    })

# --- Тесты функции load_transactions_from_excel ---

@pytest.mark.parametrize("file_path, expected_rows", [
    (None, 10),
    ("custom/path/sample.xlsx", 10)
])
def test_load_transactions_from_excel(sample_excel_file, file_path, expected_rows):
    with mock.patch.object(Path, "exists", return_value=True), \
         mock.patch("pandas.read_excel", return_value=pd.DataFrame({
             'Дата платежа': ['01.01.2020']*10,
             'Категория': ['Test']*10,
             'Сумма платежа': range(10)
         })):
        df = load_transactions_from_excel(file_path or sample_excel_file)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == expected_rows

def test_load_transactions_from_excel_file_not_found():
    with mock.patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            load_transactions_from_excel("nonexistent.xlsx")

# --- Тесты функции spending_by_category ---

@pytest.mark.parametrize("category, date, expected_result", [
    ("Супермаркет", "23.12.2018", pd.DataFrame({"Дата платежа": ["December 2018"], "Сумма платежа": [-1000]})),
    ("Транспорт", "23.12.2018", pd.DataFrame({"Дата платежа": ["November 2018"], "Сумма платежа": [-500]})),
])
def test_spending_by_category(category, date, expected_result, sample_transactions):
    with mock.patch("pandas.to_datetime", lambda x, format: pd.Series([datetime.strptime(v, format) for v in x])):
        result = spending_by_category(sample_transactions.copy(), category, date)
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))

# --- Тесты декоратор report_writer ---

@pytest.fixture
def mocked_open():
    with mock.patch("builtins.open", mock.mock_open()) as m:
        yield m

@pytest.mark.parametrize("filename, expected_calls", [
    (None, True),
    ("custom_report.json", True)
])
def test_report_writer(mocked_open, filename, expected_calls):
    @report_writer(filename)
    def dummy_function():
        return pd.DataFrame({"key": ["value"]})

    dummy_function()  # Просто вызываем функцию, результат игнорируем
    if expected_calls:
        mocked_open.assert_called_once()
    else:
        mocked_open.assert_not_called()