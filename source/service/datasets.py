"""
Defines class that hides the logic/path for saving and loading specific datasets
used across this project, as well as providing a brief description for each dataset.

To define a new dataset, create a property in Datasets.__init__() following the existing patthern.

The DATA variable is assigned an instance of the Datasets class and can be imported into other
scripts/notebooks.

To load the dataset called `the_dataset`, use the following code:

```
from source.services.data import DATA
df = DATA.the_dataset.load()
```

To save the dataset called `the_dataset`, use the following code:

```
from source.services.data import DATA

df = ...logic..
DATA.the_dataset.save(df)
```
"""
import yaml
from source.library.datasets_base import DataPersistence, DatasetsBase


class Datasets(DatasetsBase):
    """Defines the datasets available to the project."""

    raw__credit: DataPersistence
    credit: DataPersistence

# create a global object that can be imported into other scripts
with open('/code/datasets.yml') as handle:
    yaml_data = yaml.safe_load(handle)

DATA = Datasets(dataset_info=yaml_data)

# ensure all names got set properly
assert all(getattr(DATA, x).name == x for x in DATA.datasets)
