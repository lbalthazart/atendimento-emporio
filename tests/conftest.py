import pytest
from pathlib import Path
from src.config import settings
from src.database.loader import init_database

@pytest.fixture(scope="session", autouse=True)
def setup_global_test_db(tmp_path_factory):
    """Inicializa banco SQLite em diretório temporário para a sessão de testes."""
    test_db = tmp_path_factory.mktemp("db") / "test_emporio.sqlite3"
    init_database(db_path=test_db)
    settings.DATABASE_PATH = test_db
    return test_db
