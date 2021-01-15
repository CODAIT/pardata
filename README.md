# PyDAX (Under Development)

[![Pyversions](https://img.shields.io/pypi/pyversions/pydax.svg?style=flat-square)](https://pypi.python.org/pypi/pydax)
![PyPI](https://img.shields.io/pypi/v/pydax.svg)
![Runtime Tests](https://github.com/codait/pydax/workflows/Runtime%20Tests/badge.svg)
![Lint](https://github.com/codait/pydax/workflows/Lint/badge.svg)
![Docs](https://github.com/codait/pydax/workflows/Docs/badge.svg)
![Development Environment](https://github.com/codait/pydax/workflows/Development%20Environment/badge.svg)

PyDAX is a Python API that enables easy, pragmatic, and elegant programmatical downloading and loading of datasets.

## Install the Package & its Dependencies

To install the latest version of PyDAX, run

```shell
pip install -U git+https://github.com/codait/pydax
```

Alternatively, if you have downloaded the source, switch to the source directory (same directory as this README file, `cd /path/to/pydax-source`) and run

```shell
pip install -U .
```

## Quick Start

Import the package and load a dataset. PyDAX will download [WikiText-103](https://developer.ibm.com/exchanges/data/all/wikitext-103/) dataset (version `1.0.1`) if it's not already downloaded, and then load it.
```python
import pydax
wikitext103_data = pydax.load_dataset('wikitext103')
```

View available PyDAX datasets and their versions.
```python
pydax.list_all_datasets()
# {'claim_sentences_search': ('1.0.2',), ..., 'wikitext103': ('1.0.1',)}
```

To view your globally set configs for PyDAX, such as your default data directory, use `get_config`.
```python
pydax.get_config()
# Config(DATADIR=PosixPath('dir/to/dowload/load/from'), ..., DATASET_SCHEMA_URL='file/to/load/datasets/from')
```

By default, `load_dataset` downloads to and loads from `~/.pydax/data/<dataset-name>/<dataset-version>/`. To change the default data directory, use `pydax.init`.
```python
pydax.init(DATADIR='new/dir/to/dowload/load/from')
```

Load a previously downloaded dataset using `load_dataset`. With the new default data dir set, PyDAX now searches for the [Groningen Meaning Bank](https://developer.ibm.com/exchanges/data/all/groningen-meaning-bank/) dataset (version `1.0.2`) in `new/dir/to/dowload/load/from/gmb/1.0.2/`.
```python
gmb_data = load_dataset('gmb', version='1.0.2', download=False)  # assuming GMB dataset was already downloaded
```

## Notebooks

For a more extensive look at PyDAX functionality, check out these notebooks:
* [Early PyDAX Features Walkthrough](https://github.com/CODAIT/pydax/blob/master/docs/notebooks/pydax-mvp-demo.ipynb)
