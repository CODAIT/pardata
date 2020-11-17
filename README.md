# PyDAX (Under Development)

A simple Python API for downloading and loading datasets from IBM's [Data Asset Exchange](https://ibm.biz/data-exchange).

## Install the Package & its Dependencies

```shell
pip install -U -e .
```

## Simple Examples

Import the full package.
```python
import pydax
```

View available PyDAX datasets and their versions.
```python
from pydax.dataset import list_all_datasets
list_all_datasets()
# {'gmb': ('1.0.2',), 'wikitext103': ('1.0.1',)}
```

Load a dataset into memory as a dict composed of subdatasets using `load_dataset()`. By default, `load_dataset()` will download the dataset to your default data directory if it is not already present there. If the `version` parameter is not specified, the dataset's latest version available on PyDAX is assumed. In this example, PyDAX will download the [GMB](https://developer.ibm.com/exchanges/data/all/groningen-meaning-bank/) dataset (version `1.0.2`) to `~/.pydax/data/gmb/1.0.2/` and loads its subdatasets into `gmb_data`. 
```python
from pydax.dataset import load_dataset
gmb_data = load_dataset('gmb')
```

By default, `load_dataset()` downloads to and loads from `~/.pydax/data/<dataset-name>/<dataset-version>/`. To change the default data directory, use `pydax.init`.
```python
pydax.init(DATADIR='new/dir/to/dowload/load/from')
```

To view your globally set configs for PyDAX, such as your default data directory, use `get_config()`.
```python
pydax.get_config()
# Config(DATADIR=PosixPath('new/dir/to/dowload/load/from'))
```

Load a previously downloaded dataset using `load_dataset`. With the new default data dir set, PyDAX now searches for the [WikiText-103](https://developer.ibm.com/exchanges/data/all/wikitext-103/) dataset (version `1.0.1`) in `new/dir/to/dowload/load/from/wikitext103/1.0.1/`.
```python
wikitext103_data = load_dataset('wikitext103', version='1.0.1', download=False)  # assuming wikitext103 was already downloaded
```
