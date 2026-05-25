# -*- coding: utf-8 -*-
"""
Simple addition to zipfile options that allows for intuitive control over
zipfile internal uses

"""

import zipfile
from typing import Self, Iterable
import os
from functools import partial
import re


def member_endswith(member: zipfile.ZipInfo,
                    match_key: str) -> bool:
    return member.filename.endswith(match_key)

class ZipIndex:
    
    def __repr__(self) -> str:
        return (f"ZipIndex(zipfile_path={self.zipfile_path}, "
                         f"member_name={self.member_name})")
    
    def __init__(self, 
                 zipfile_path: str,
                 member_name: str) -> Self:
        
        self.zipfile_path = zipfile_path
        self.member_name = member_name
        
    def open(self) -> os.PathLike:
        self.zf = zipfile.ZipFile(self.zipfile_path, 'r')
        matched_file = max(self.zf.filelist,
                           key=partial(member_endswith, 
                                       match_key=self.member_name))
        self.fid = self.zf.open(matched_file, 'r')
        return self.fid
    
    def suffix(self):
        m = re.match(r"^.*(\.\w+)$", self.member_name)
        if m:
            return m.group(1)
        return ""
    
    
    def __enter__(self) -> os.PathLike:
        return self.open()
    
    def __exit__(self, etype, e, tb) -> None:
        self.fid.close()
        self.zf.close()
        return None
    

    @classmethod
    def factory(cls, zipfile_path: str) -> dict[str, Self]:
        with zipfile.ZipFile(zipfile_path, 'r') as zf:
            output = {
                member.filename : cls(zipfile_path, 
                                      member.filename.split("/")[-1]) 
                for member in zf.filelist
                if not member.filename.endswith("/")}
        return output
    
    @classmethod
    def categorical_factory(cls, 
                            zipfile_path: str,
                            categories: dict[str, Iterable[dict[int, bytes]]]) -> dict[str, tuple[Self]]:
        """
        Provides a factory for categorizing internal files in a zipfile.ZipFile
        Must match all conditions of at least one category to be included in 
        the output.

        Parameters
        ----------
        zipfile_path : str
            Path to the zipfile.
        categories : dict[str, Iterable[dict[int, bytes]]]
            Dictionary definition of bytes-wise matching for type detection.
            Ex: {"empty" : [{0: b""}]}
        Returns
        -------
        dict[str, tuple[Self]]
            {category : tuple[ZipIndex]}.

        """
        assert categories
        output = {cat: [] for cat in categories}
        with zipfile.ZipFile(zipfile_path, 'r') as zf:
            for category, definition in categories.items():
                for member in zf.filelist:
                    if member.filename.endswith("/"): continue
                    with zf.open(member, 'r') as fid:
                        matched = []
                        for position, condition in definition.items():
                            fid.seek(position, 0)
                            if len(condition) == 0:
                                b = fid.read()
                            else:
                                b = fid.read(len(condition))
                            matched.append((b == condition))
                        if all(matched):
                            output[category].append(cls(zipfile_path, 
                                                        member.filename.split("/")[-1]))
        return output

idx = ZipIndex.categorical_factory(zipfile_path='C:/dev/data.zip', 
                                   categories={"empty": {0: b""},
                                               "bin" : {0: b"BIN"}})