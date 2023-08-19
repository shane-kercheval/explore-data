"""
Defines the base classes that hide the logic/path for saving and loading specific
datasets used across this project, as well as providing a brief description for each dataset.
"""

import dataclasses
import os
import datetime
import logging
import pickle
from abc import ABC, abstractmethod
import pandas as pd


class DataPersistence(ABC):
    """
    Wraps the logic of saving/loading/describing a given dataset.
    Meant to be subclassed with specific types of loaders (e.g. pickle, csv, database, etc.).
    """

    def __init__(self, description: str, dependencies: list, cache: bool = False):
        """
        Args:
            description: description of the dataset.
            dependencies: dependencies of the dataset.
            cache: if True, return cached data on subsequent calls of `load()`.
        """
        self.description = description
        self.dependencies = dependencies
        self.cache = cache
        self.name = None  # this is set dynamically
        self._cached_data = None


    def clear_cache(self) -> None:
        """Clears the cache so that the next call to `load()` reloads data."""
        self._cached_data = None

    @abstractmethod
    def _load(self) -> object:
        """Overriding function should contain the logic for loading the data."""

    @abstractmethod
    def _save(self, data: object) -> None:
        """Overriding function should contain the logic for saving the data."""

    def load(self) -> object:
        """Loads the data according to caching rules."""
        assert self.name
        if self.cache:
            if self._cached_data is None:
                self._cached_data = self._load()
            return self._cached_data
        return self._load()

    def save(self, data: object) -> None:
        """Loads the data and caches accordingly."""
        assert self.name
        if self.cache:
            self._cached_data = data
        self._save(data)


class FileDataPersistence(DataPersistence):
    """
    Class that wraps the logic of saving/loading/describing a given dataset to the file-system.
    Adds logic for backing up datasets if they are being saved and already exist (i.e. renaming
    the file with a timestamp).
    Meant to be subclassed with specific types of loaders (e.g. pickle, csv, etc.).
    """

    def __init__(self, description: str, dependencies: list, directory: str, cache: bool = False):
        """
        Args:
            description: description of the dataset.
            dependencies: dependencies of the dataset.
            directory: the directory of the dataset.
            cache: if True, return cached data on subsequent calls of `load()`.
        """
        super().__init__(description=description, dependencies=dependencies, cache=cache)
        self.directory = directory

    @abstractmethod
    def _load(self) -> object:
        """Overriding function should contain the logic for loading the data."""

    @abstractmethod
    def _save(self, data: object) -> None:
        """Overriding function should contain the logic for saving the data."""

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension to use for the path (e.g. '.csv' or '.pkl')."""

    @property
    def path(self) -> str:
        """Full path (directory and file name) to load/save."""
        return os.path.join(self.directory, self.name + self.file_extension)

    def load(self) -> object:
        """Loads the data according to caching rules."""
        assert self.name
        logging.info(f"Loading data `{self.name}` from `{self.path}`")
        return super().load()

    def save(self, data: object) -> None:
        """
        Saves the data. If the file already exists, that file will be renamed with a appended
        timestamp.
        """
        assert self.name
        logging.info(f"Saving data `{self.name}` to `{self.path}`")
        # if the file already exists, save it to another name
        if os.path.isfile(self.path):
            timestamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            new_name = self.path + '.' + timestamp
            logging.info(f"Backing up current data `{self.name}` to `{new_name}`")
            os.rename(self.path, new_name)
        super().save(data)


class PickledDataLoader(FileDataPersistence):
    """Class that wraps the logic of saving/loading/describing a given dataset."""

    def __init__(self, description: str, dependencies: list, directory: str, cache: bool = False):
        """
        Args:
            description: description of the dataset.
            dependencies: dependencies of the dataset.
            directory:
                the directory to save to and load from. NOTE: this should **not** contain the file
                name which is assigned at a later point in time based on the property name in the
                `Datasets` class.
            cache: if True, return cached data on subsequent calls of `load()`.
        """
        super().__init__(
            description=description,
            dependencies=dependencies,
            directory=directory,
            cache=cache,
        )

    @property
    def file_extension(self) -> str:
        """Returns the corresponding File Extension."""
        return '.pkl'

    def _load(self) -> object:
        with open(self.path, 'rb') as handle:
            return pickle.load(handle)

    def _save(self, data: object) -> None:
        with open(self.path, 'wb') as handle:
            pickle.dump(data, handle)


class CsvDataLoader(FileDataPersistence):
    """Class that wraps the logic of saving/loading/describing a given dataset."""

    def __init__(self, description: str, dependencies: list, directory: str, cache: bool = False):
        """
        Args:
            description: description of the dataset
            dependencies: dependencies of the dataset
            directory:
                the path to save to and load from. NOTE: this should **not** contain the file name
                which is assigned at a later point in time based on the property name in the
                `Datasets` class.
            cache: if True, return cached data on subsequent calls of `load()`.
        """
        super().__init__(
            description=description,
            dependencies=dependencies,
            directory=directory,
            cache=cache,
        )

    @property
    def file_extension(self) -> str:
        """Returns the corresponding File Extension."""
        return '.csv'

    def _load(self) -> object:
        return pd.read_csv(self.path)

    def _save(self, data: pd.DataFrame) -> None:
        data.to_csv(self.path, index=None)


@dataclasses.dataclass()
class DatasetsBase:
    """
    Defines all of the datasets available globally to the project.
    NOTE: in overridding the base class, call __init__() after defining properties.
    """

    def __init__(self, dataset_info: dict) -> None:
        """
        Create the DataPersistence objects for each field defined in the child class. Ensure the
        fields created in the child class match the fields/keys in `dataset_info`.
        """
        di_names = list(dataset_info.keys())
        assert len(di_names) == len(set(di_names))  # ensure no duplicates
        field_names = list(self.__annotations__.keys())
        assert di_names == field_names

        for field_name in field_names:
            info = dataset_info[field_name]
            persist_class_name = info.pop('type')
            persist_obj = globals()[persist_class_name](**info)
            persist_obj.name = field_name
            setattr(self, field_name, persist_obj)

    @property
    def datasets(self) -> list[str]:
        """Returns the names of the datasets available."""
        ignore = {'datasets', 'descriptions', 'dependencies'}
        return [
            attr for attr in dir(self)
            if attr not in ignore and isinstance(getattr(self, attr), DataPersistence)
        ]

    @property
    def descriptions(self) -> dict[str]:
        """Returns the names and descriptions of the datasets available."""
        return [
            {
                "dataset": x,
                "description": getattr(self, x).description,
            }
            for x in self.datasets
        ]

    @property
    def dependencies(self) -> dict[str]:
        """Returns the names and dependencies of the datasets available."""
        return [
            {
                "dataset": x,
                "dependencies": getattr(self, x).dependencies,
            }
            for x in self.datasets
        ]
