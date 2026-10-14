"""
Pytest fixtures for CreditLens test suite.
"""

import os
import pytest
import pandas as pd


@pytest.fixture(scope="session")
def project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def processed_data_dir(project_root):
    return os.path.join(project_root, "data", "processed")


@pytest.fixture(scope="session")
def clean_industry_df(processed_data_dir):
    path = os.path.join(processed_data_dir, "credit_clean.csv")
    df = pd.read_csv(path)
    df["reporting_date"] = pd.to_datetime(df["reporting_date"])
    return df


@pytest.fixture(scope="session")
def metrics_df(processed_data_dir):
    path = os.path.join(processed_data_dir, "sector_monthly_metrics.csv")
    df = pd.read_csv(path)
    df["reporting_date"] = pd.to_datetime(df["reporting_date"])
    return df


@pytest.fixture(scope="session")
def concentration_df(processed_data_dir):
    path = os.path.join(processed_data_dir, "industry_concentration_monthly.csv")
    return pd.read_csv(path)
