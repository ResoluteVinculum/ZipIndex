# -*- coding: utf-8 -*-
"""
Simple addition to zipfile options that allows for intuitive control over
zipfile internal uses

"""

import zipfile
from typing import Self
import os
from functools import partial
import re


def member_endswith(member: zipfile.ZipInfo,
                    match_key: str) -> bool:
    """
    Picklable method for compatibility

    """
    return member.filename.endswith(match_key)

class ZipItem:
    """
    ZipItem
    --------
    Object for selecting a single file out of a ZipFile object with direct 
    access.
    
    """
    
    def __repr__(self) -> str:
        return (f"ZipItem(zipfile_path={self.zipfile_path}, "
                         f"member_name={self.member_name})")
    
    def __init__(self, 
                 zipfile_path: str,
                 member_name: str) -> Self:
        """
        Initialize a ZipItem object.

        Parameters
        ----------
        zipfile_path : str
            Path to zipfile.ZipFile.
        member_name : str
            Unique suffix for identifying a member in the zipfile.

        Returns
        -------
        Self
            
        """
        
        self.zipfile_path = zipfile_path
        self.member_name = member_name
        
    def open(self, mode:str = 'r') -> os.PathLike:
        """
        Opens the internal file to be read. Modes are binary modes.

        Parameters
        ----------
        mode : str, optional
            File mode 'r'|'a'|'w'. The default is 'r'.

        Returns
        -------
        os.PathLike
            Binary open mode access to internal file.

        """
        self.zf = zipfile.ZipFile(self.zipfile_path, mode)
        matched_file = max(self.zf.filelist,
                           key=partial(member_endswith, 
                                       match_key=self.member_name))
        self.fid = self.zf.open(matched_file, mode)
        return self.fid
    
    def close(self):
        """
        Releases file hooks.

        """
        self.fid.close()
        self.zf.close()
    
    def suffix(self) -> str:
        """
        File extension of internal file

        """
        m = re.match(r"^.*(\.\w+)$", self.member_name)
        if m:
            return m.group(1)
        return ""
    
    
    def __enter__(self) -> os.PathLike:
        return self.open()
    
    def __exit__(self, etype, e, tb) -> None:
        self.close()
        return None
    

    @classmethod
    def factory(cls, zipfile_path: str) -> dict[str, Self]:
        """
        Returns a index of individual files inside of the provided
        zipfile, no directories.

        Parameters
        ----------
        zipfile_path : str

        Returns
        -------
        dict[str, Self]

        """
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
                            categories: dict[str, dict[bytes, int]]) -> dict[str, tuple[Self]]:
        """
        Provides a factory for categorizing internal files in a zipfile.ZipFile
        Must match all conditions of at least one category to be included in 
        the output.

        Parameters
        ----------
        zipfile_path : str
            Path to the zipfile.
        categories : dict[str, dict[bytes, int]]
            Dictionary definition of bytes-wise matching for type detection.
            
            Ex: {"empty" : [{0: b""}]}
        Returns
        -------
        dict[str, tuple[Self]]
            {category : list[ZipItem]}.

        """
        assert categories
        output = {cat: [] for cat in categories}
        index = cls.factory(zipfile_path)
        for category, definition in categories.items():
            for name, member in index.items():
                with member.open('r') as fid:
                    matched = []
                    for condition, position in definition.items():
                        fid.seek(position, 0)
                        if len(condition) == 0:
                            b = fid.read()
                        else:
                            b = fid.read(len(condition))
                        matched.append((b == condition))
                    if all(matched):
                        output[category].append(member)
        return output

idx = ZipItem.categorical_factory(zipfile_path='C:/dev/data.zip', 
                                   categories={"empty": {b"": 0},
                                               "bin" : {b"BIN": 0}})