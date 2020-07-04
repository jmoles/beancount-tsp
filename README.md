# beancount-tsp

Tools I have for managing the US Thrift Savings Plan (TSP) with [beancount](http://furius.ca/beancount/). The tools are:

  * Import plugin [__init__.py](__init__.py). See also, beancount [importer documentation](https://docs.google.com/document/d/11EwQdujzEo2cxqaF5PgxCEZXWfKKQCYSMfdJowp_1S8/edit).
  * Price fetch tool [tspparser.py](tspparser.py): Grabs the latest prices from the TSP web site and converts it into a beancount format.

# Usage

1. Clone this repository into your beancount importers folder. For example,
```shell
git clone git@github.com:jmoles/beancount-tsp.git tsp
```
2. In your import configuration file, add a the python import directive that references this repo. This assumes you placed the repo in a folder called "importers" relative to your beancount import configuration file.
```python
from importers import tsp
```
3. In the import configuration file, add a beancount import directive:
```python
    tsp.Importer(
        cash_account="Assets:US:TSP:Cash",
        tsp_root="Assets:US:TSP"
        ),
```
