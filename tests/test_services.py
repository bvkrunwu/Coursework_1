import json

import pytest

from src.services import analyze_cashback_categories


@pytest.fixture(scope='module')
def sample_data():
    return [
        {"date": "2023-04-15", "category": "Продукты", "amount": "1000"},
        {"date": "2023-04-20", "category": "Развлечения", "amount": "500"},
        {"date": "2023-04-25", "category": "Транспорт", "amount": "300"},
        {"date": "2023-05-01", "category": "Продукты", "amount": "800"}
    ]

@pytest.mark.parametrize('year, month, expected_output', [
    (2023, 4, {"Продукты": 50.0, "Развлечения": 25.0, "Транспорт": 15.0}),
    (2023, 5, {"Продукты": 40.0}),  # Исправлен ожидаемый результат для мая
])
def test_analyze_cashback_categories(sample_data, year, month, expected_output):
    result = analyze_cashback_categories(sample_data, year, month)
    parsed_result = json.loads(result)
    assert parsed_result == expected_output

@pytest.mark.parametrize('invalid_data, expected_output', [
    ([{"date": "2023-04-15", "category": "Продукты"}], {}),
    ([{"date": "2023-04-15", "amount": "1000"}], {}),
])
def test_missing_fields(invalid_data, expected_output):
    result = analyze_cashback_categories(invalid_data, 2023, 4)
    parsed_result = json.loads(result)
    assert parsed_result == expected_output

@pytest.mark.parametrize('invalid_amount, expected_output', [
    ([{"date": "2023-04-15", "category": "Продукты", "amount": "abc"}], {}),
])
def test_invalid_amount_format(invalid_amount, expected_output):
    result = analyze_cashback_categories(invalid_amount, 2023, 4)
    parsed_result = json.loads(result)
    assert parsed_result == expected_output

def test_empty_input():
    empty_data = []
    result = analyze_cashback_categories(empty_data, 2023, 4)
    parsed_result = json.loads(result)
    assert parsed_result == {}
