import pytest
from src.utils import determine_greeting, calculate_card_data, retrieve_top_transactions
from unittest.mock import patch
import pandas as pd

@pytest.fixture
def mock_dataframe():
    data = {
        "Дата операции": ["01.10.2023", "02.10.2023", "03.10.2023"],
        "Номер карты": ["1234567890123456", "1234567890123457", "1234567890123458"],
        "Сумма операции": [100.0, 200.0, 300.0]
    }
    df = pd.DataFrame(data)
    with patch('pandas.read_excel', return_value=df):
        yield

@pytest.mark.parametrize("datetime_str, expected_greeting", [
    ("01-10-2023 08:00:00", "Доброе утро"),
    ("01-10-2023 14:00:00", "Добрый день"),
    ("01-10-2023 20:00:00", "Добрый вечер"),
    ("01-10-2023 02:00:00", "Доброй ночи"),
])
def test_determine_greeting(datetime_str, expected_greeting):
    greeting = determine_greeting(datetime_str)
    assert greeting == expected_greeting

def test_calculate_card_data(mock_dataframe):
    start_date = "2023-10-01"
    end_date = "2023-10-03"
    result = calculate_card_data(start_date, end_date)
    assert len(result) == 3
    assert result[0]["last_digits"] == "3456"
    assert result[0]["cashback"] == 1.0

def test_retrieve_top_transactions(mock_dataframe):
    start_date = "2023-10-01"
    end_date = "2023-10-03"
    result = retrieve_top_transactions(start_date, end_date)
    assert len(result) == 3
    assert result[0]["Сумма операции"] == 300.0