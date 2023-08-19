"""Defines test fixtures for pytest unit-tests."""
import pytest
from source.library.datasets_base import DatasetsBase, DataPersistence


class TestDatasets(DatasetsBase):
    """Creates a fake/mock dataset."""

    dataset_1: DataPersistence
    other_dataset_2: DataPersistence
    dataset_3_csv: DataPersistence


@pytest.fixture()
def datasets_fake_cache() -> TestDatasets:
    """Returns fake dataset with cache turned on."""
    import yaml
    file_name = '/code/tests/test_files/test_datasets/datasets_cache.yml'
    with open(file_name) as handle:
        yaml_data = yaml.safe_load(handle)
    return TestDatasets(dataset_info=yaml_data)


@pytest.fixture()
def datasets_fake_no_cache() -> TestDatasets:
    """Returns fake dataset with cache turned off."""
    import yaml
    file_name = '/code/tests/test_files/test_datasets/datasets_no_cache.yml'
    with open(file_name) as handle:
        yaml_data = yaml.safe_load(handle)
    return TestDatasets(dataset_info=yaml_data)
