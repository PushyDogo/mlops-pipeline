from pathlib import Path


def test_expected_project_directories_exist() -> None:
    root = Path(__file__).resolve().parents[1]

    expected_directories = [
        "data",
        "src/features",
        "src/training",
        "src/serving",
        "src/monitoring",
        "pipelines/airflow_dags",
        "pipelines/kfp_pipelines",
        "infra/k8s",
        "infra/terraform",
        "notebooks",
        "tests",
    ]

    missing = [path for path in expected_directories if not (root / path).is_dir()]

    assert missing == []
