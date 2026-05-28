# -*- coding: utf-8 -*-
"""
Simple addition to zipfile options that allows for intuitive control over
zipfile internal uses

"""

import zipfile, tarfile
from typing import Self, Iterable
import os
import re

def member_match(member: str,
                 match_pattern: str) -> bool:
    """
    Picklable method for compatibility

    """
    if not match_pattern.endswith("$"):
        match_pattern += "$"
    if not match_pattern.startswith("^"):
        match_pattern = "^" + match_pattern
    return bool(re.match(match_pattern, member))

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
        
        self.compression_class = self.detect_compression_type(zipfile_path)
        self._kwd, self._access, self._read = self.get_compressed_member_keywords(zipfile_path)
        
        with self.compression_class(self.zipfile_path, 'r') as zf:
            members = [m for m in getattr(zf, self._kwd)()
                       if member_match(m, self.member_pattern)]
        if len(members) == 1:
            self.member_name = members[0]
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
        self.zf = self.compression_class(self.zipfile_path, mode)
        kwargs = {mode: "r"} if self.compression_class is zipfile.ZipFile else {}
        self.fid = getattr(self.zf, self._read)(self.member_name, **kwargs)
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
        p, ext = os.path.splitext(self.member_name)
        return ext
    
    
    def __enter__(self) -> os.PathLike:
        return self.open()
    
    def __exit__(self, etype, e, tb) -> None:
        return self.close()
    
    @classmethod
    def detect_compression_type(cls, zipfile_path:str):
        if zipfile.is_zipfile(zipfile_path):
            compression_class = zipfile.ZipFile
        elif tarfile.is_tarfile(zipfile_path):
            compression_class = tarfile.TarFile
        if not compression_class:
            raise NotImplementedError(f"No supported compression types for {zipfile_path}!")
        
        return compression_class
    
    @classmethod
    def get_compressed_member_keywords(cls, zipfile_path:str):
        if zipfile.is_zipfile(zipfile_path):
            members = "namelist", "getinfo", "open"
        elif tarfile.is_tarfile(zipfile_path):
            members = "getnames", "getmember", "extractfile"

        if not members:
            raise NotImplementedError(f"No supported compression types for {zipfile_path}!")
        
        return members
    
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
        compression_class = cls.detect_compression_type(zipfile_path)
        method, access, read = cls.get_compressed_member_keywords(zipfile_path)
        if not categories:
            with compression_class(zipfile_path, 'r') as zf:
                for member_name in getattr(zf, method)():
                    member = getattr(zf, access)(member_name)
                    if member_name.endswith("/"): continue
                    if pattern:
                        if not re.match(pattern, member_name):
                            continue
                    name = re.escape(member_name)
                    item = cls(zipfile_path, name)
                    if extensions:
                        if item.suffix not in extensions:
                            continue
                    output[member_name] = item
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
    index = ZipItem.factory('C:/dev/data.tar')
    a = index['data/file1']
    a.open()
