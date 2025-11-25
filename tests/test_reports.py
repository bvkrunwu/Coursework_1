import logging  # Необходим для проверки логирования
from unittest.mock import patch

import pandas as pd
import pytest

# Импортируем необходимые компоненты из реального модуля
from src.reports import logs_dir, project_root, reports_dir, spending_by_category


# Фикстура для временного рабочего окружения
@pytest.fixture(scope='session')
def temp_dirs(tmpdir_factory):
    """Создает временные папки для эмуляции структуры проекта."""
    root = tmpdir_factory.mktemp('project_root')
    reports = root.mkdir('reports')
    logs = root.mkdir('logs')
    return {'root': root, 'reports': reports, 'logs': logs}

# Фикстура для замены реальных путей на временные
@pytest.fixture
def mock_paths(temp_dirs):
    """Подменяет реальные пути на временные для избежания изменений в рабочей среде."""
    with patch('src.reports.project_root', temp_dirs['root']), \
         patch('src.reports.reports_dir', temp_dirs['reports']), \
         patch('src.reports.logs_dir', temp_dirs['logs']):
        yield

# Фикстура для образца транзакций
@pytest.fixture
def sample_transactions():
    """Возвращает образец DataFrame с транзакциями."""
    return pd.DataFrame({
        "Дата платежа": ["01.01.2023", "15.01.2023", "01.02.2023"],
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Сумма платежа": [100, 200, 150]
    })

# Простые тесты базовой конфигурации проекта
def test_project_structure(mock_paths):
    """Проверяет существование директорий проекта."""
    assert project_root.exists(), "Корневая директория проекта не найдена."
    assert reports_dir.exists() and reports_dir.is_dir(), "Директория reports отсутствует."
    assert logs_dir.exists() and logs_dir.is_dir(), "Директория logs отсутствует."

# Простой тест поведения функции при отсутствии данных
def test_spending_by_category_empty(sample_transactions):
    """Проверяет поведение функции при отсутствии данных по категории."""
    result = spending_by_category(sample_transactions, "Развлечения")
    assert result.empty, "Отчёт должен быть пустым при отсутствии данных."

# Простой тест логирования
def test_spending_by_category_logging(caplog, sample_transactions):
    """Проверяет правильность логирования при формировании отчета."""
    caplog.set_level(logging.INFO)
    spending_by_category(sample_transactions, "Еда")
    assert any("Сформирован отчет о тратах по категории" in record.message for record in caplog.records), "Логирование не сработало."

# Простой тест обработки исключительной ситуации
def test_spending_by_category_invalid_date(sample_transactions):
    """Проверяет обработку некорректного формата даты."""
    with pytest.raises(ValueError):
        spending_by_category(sample_transactions, "Еда", "invalid-date-format")