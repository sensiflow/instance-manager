from src.config import parse_config, get_environment_type
from src.database.datasource import DataSource
import pytest


@pytest.fixture(scope="session")
def datasource():
    config = parse_config(get_environment_type())
    url = config["DATABASE"]["URL"]
    return DataSource(url)


def test_db_connection(datasource):
    with datasource.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1
