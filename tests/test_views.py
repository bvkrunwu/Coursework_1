import pytest
from src.views import generate_home_response
from unittest.mock import patch

@pytest.fixture
def mock_utils():
    with patch('src.views.calculate_card_data') as mock_card_data, \
         patch('src.views.retrieve_top_transactions') as mock_top_transactions, \
         patch('src.views.get_currency_rates') as mock_currency_rates, \
         patch('src.views.get_stock_prices') as mock_stock_prices:
        mock_card_data.return_value = [{"last_digits": "1234", "cashback": 10.0}]
        mock_top_transactions.return_value = [{"Сумма операции": 100.0}]
        mock_currency_rates.return_value = {"currency_rates": [{"currency": "USD", "rate": 75.0}]}
        mock_stock_prices.return_value = {"stock_prices": [{"stock": "AAPL", "price": 150.0}]}
        yield

@pytest.mark.parametrize("date_time_str, expected_greeting", [
    ("2023-10-01 08:00:00", "Доброе утро"),
    ("2023-10-01 14:00:00", "Добрый день"),
    ("2023-10-01 20:00:00", "Добрый вечер"),
    ("2023-10-01 02:00:00", "Доброй ночи"),
])
def test_generate_home_response(date_time_str, expected_greeting, mock_utils):
    response = generate_home_response(date_time_str)
    assert response["greeting"] == expected_greeting
    assert "cards" in response
    assert "top_transactions" in response
    assert "currency_rates" in response
    assert "stock_prices" in response