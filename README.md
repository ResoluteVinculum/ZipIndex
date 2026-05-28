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

# Categorical Factory
categories: dict[str, ZipItem] = ZipItem.factory(zipfile_path="...", categories={"empty" : {0 : b""}})


```