"""Tests use a reproducible temporary database, never the user's data."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("GROQ_API_KEY", "test-key")


@pytest.fixture(scope="session", autouse=True)
def generated_database(tmp_path_factory):
    import random
    import create_database
    import generate_data
    import inject_anomalies
    import add_anomalies
    import analysis_tools
    import sql_tools
    import visualization_tools

    directory = tmp_path_factory.mktemp("banking")
    database = directory / "banking.db"
    modules = [create_database, generate_data, inject_anomalies, add_anomalies,
               analysis_tools, sql_tools, visualization_tools]
    with pytest.MonkeyPatch.context() as patch:
        for module in modules:
            patch.setattr(module, "DB_PATH", database)
        for module in [inject_anomalies, add_anomalies]:
            patch.setattr(module, "GROUND_TRUTH_PATH", directory / "truth.json")
        patch.setattr(visualization_tools, "OUTPUT_DIR", directory / "outputs")
        create_database.create_database()
        random.seed(42)
        generate_data.generate_data()
        random.seed(42)
        inject_anomalies.inject_anomalies()
        random.seed(42)
        add_anomalies.add_anomalies()
        yield database
