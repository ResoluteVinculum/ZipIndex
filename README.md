# ZipIndex
Simple, pure-python object package for dealing with many files inside of
zipfiles.

# Example Usage
```python
from zipindex import ZipIndex

# Single Instance
inst = ZipIndex(zipfile_path="...", member_name="...")

# Simple Factory
members: dict[str, ZipIndex] = ZipIndex.factory(zipfile_path="...")

# Categorical Factory
categories: dict[str, ZipIndex] = ZipIndex.categorical_factory(zipfile_path="...", categories={"empty" : {0 : b""}})

# Use
with inst.open() as fid:
    data = fid.read()

```