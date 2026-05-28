# ZipIndex
Simple, pure-python object package for dealing with many files inside of
zipfiles.

# Example Usage
```python
from zipindex import ZipItem

# Single Instance
inst = ZipItem(zipfile_path="...", member_name="...")

# Simple Factory
members: dict[str, ZipItem] = ZipItem.factory(zipfile_path="...")

# Patterned Factory - Requires some knowledge of the contents
files_patt: dict[str, ZipItem] = ZipItem.factory(zipfile_path="...",
                                                 pattern=r"^data/.*.csv$")

# File Extension Factory
files_ext = dict[str, ZipItem] = ZipItem.factory(zipfile_path="...", 
                                                 extensions=[".csv"])

# Categorical Factory
categories: dict[str, list[ZipItem]] = ZipItem.factory(zipfile_path="...",
                                                       categories={"empty" : {0 : b""}})

```

## Behavior
The `categories` factory keyword will always return a dictionary with lists of items
as its values, while without the factory will always return a dictionary
with items as values instead.