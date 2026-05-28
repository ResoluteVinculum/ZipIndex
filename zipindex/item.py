# -*- coding: utf-8 -*-
"""
Simple addition to zipfile options that allows for intuitive control over
zipfile internal uses

"""

import zipfile
from typing import Self, Iterable
import os
import re

def member_match(member: zipfile.ZipInfo,
                 match_pattern: str) -> bool:
    """
    Picklable method for compatibility

    """
    if not match_pattern.endswith("$"):
        match_pattern += "$"
    if not match_pattern.startswith("^"):
        match_pattern = "^" + match_pattern
    return bool(re.match(match_pattern, member.filename))

class ZipItem:
    """
    ZipItem
    --------
    Object for selecting a single file out of a ZipFile object with direct 
    access.
    
    """
    
    def __init__(self, 
                 zipfile_path: str,
                 member_pattern: str) -> Self:
        """
        Initialize a ZipItem object.

        Parameters
        ----------
        zipfile_path : str
            Path to zipfile.ZipFile.
        member_pattern : str
            Match pattern for internal file matching

        Returns
        -------
        Self
            
        """
        
        self.zipfile_path = zipfile_path
        self.member_pattern = member_pattern
        self._pointer = 0

        with zipfile.ZipFile(self.zipfile_path, 'r') as zf:
            members = [m.filename for m in zf.filelist
                       if member_match(m, self.member_pattern)]
        if len(members) == 1:
            self.member_name = members[0]
            self.Path = zipfile.Path(self.zipfile_path, self.member_name)
        elif len(members) > 1:
            ambig = "\n  - " + "\n  - ".join(members)
            raise ValueError(f"Pattern: '{member_pattern}' is ambiguous in '{zipfile_path}'!\nMembers:{ambig}")
        else:
            raise ValueError(f"Pattern: '{member_pattern}' matches no members of '{zipfile_path}'!")

    def __repr__(self) -> str:
        return f"ZipItem(zipfile_path={self.zipfile_path}, member_pattern={re.escape(self.member_name)})"

    def __str__(self) -> str:
        return self.member_name

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
        file = self.zf.getinfo(self.member_name)
        self.fid = self.zf.open(file, mode)
        return self.fid
    
    def seek(self, 
             offset:int=0,
             whence:int = 0) -> int:
        with self.open():
            self._pointer = self.fid.seek(offset, whence)
        return self._pointer
    
    def read(self,
             n:int = None):
        with self.open():
            self.fid.seek(self._pointer)
            out = self.fid.read(n)
            self._pointer = self.fid.tell()
        return out
    
    def extract(self, destination_directory) -> None:
        with self.open():
            self.zf.extract(self.member_name, destination_directory)
        return
    
    def close(self) -> None:
        """
        Releases file hooks.

        """
        self.fid.close()
        self.zf.close()
        return
    
    @property
    def suffix(self) -> str:
        """
        File extension of internal file

        """
        return self.Path.suffix
    
    
    def __enter__(self) -> os.PathLike:
        return self.open()
    
    def __exit__(self, etype, e, tb) -> None:
        return self.close()
    

    @classmethod
    def factory(cls, 
                zipfile_path: str,
                *,
                pattern: str = None,
                categories: dict[str, dict[bytes, int]] = None,
                extensions: Iterable[str] = None) -> dict[str, Self|list[Self]]:
        """
        Returns a index of individual files inside of the provided
        zipfile, no directories.

        Parameters
        ----------
        zipfile_path : str
        pattern : str
            Regex Match Pattern for filenames
        categories : dict[str, dict[bytes, int]]
            Dictionary definition of bytes-wise matching patterns for user
            categories. If provided, only items that match every condition of
            a given category will be returned. The default is None.
        extensions : Iterable[str]
            List of extensions (including the ".") to filter to.

        Returns
        -------
        dict[str, Self|list[Self]]

        """
        output = {}
        if not categories:
            with zipfile.ZipFile(zipfile_path, 'r') as zf:
                for member in zf.filelist:
                    if member.filename.endswith("/"): continue
                    if pattern:
                        if not re.match(pattern, member.filename):
                            continue
                    name = re.escape(member.filename)
                    item = cls(zipfile_path, name)
                    if extensions:
                        if item.suffix not in extensions:
                            continue
                    output[member.filename] = item
        else:
            output = {cat : [] for cat in categories}
            index = cls.factory(zipfile_path, pattern=pattern, extensions=extensions)
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
                            matched.append( (b == condition) )
                        if extensions:
                            matched.append( (member.suffix in extensions) )
                        if all(matched):
                            output[category].append(member)
        return output
        with zipfile.ZipFile(zipfile_path, 'r') as zf:
            output = {
                member.filename : cls(zipfile_path, 
                                      member.filename.split("/")[-1]) 
                for member in zf.filelist
                if not member.filename.endswith("/")}
        return output
    

if __name__ == "__main__":
    pass