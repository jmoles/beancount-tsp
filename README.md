# beancount-tsp

Import plugin for the double-entry plain text acount tool, [beancount](http://furius.ca/beancount/). See also, beancount [importer documentation](https://docs.google.com/document/d/11EwQdujzEo2cxqaF5PgxCEZXWfKKQCYSMfdJowp_1S8/edit).

# Usage

1. Clone this repository into your beancount importers folder. For example,
```shell
git clone git@github.com:jmoles/beancount-tsp.git tsp
```
2. In your import configuration file, add a the python import directive that referenes this repo. This assumes you placed the repo in a folder called "importers" relative to your beancount import configuration file.
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
