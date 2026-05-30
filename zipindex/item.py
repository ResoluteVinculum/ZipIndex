# -*- coding: utf-8 -*-
"""
Simple addition to zipfile options that allows for intuitive control over
zipfile internal uses

"""

import zipfile
import tarfile
from typing import Self, Iterable
import os
import re

from zipindex.utils import HybridMethod


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
        self.__pointer = 0
        self.zf = None
        self.fid = None

        self.compression_class = self.get_compression_class(zipfile_path)

        members = [m for m in self.get_member_names()
                   if member_match(m, self.member_pattern)]
        if len(members) == 1:
            self.member_name = members[0]
        elif len(members) > 1:
            ambig = "\n  - " + "\n  - ".join(members)
            raise ValueError(f"Pattern: '{member_pattern}' is ambiguous in "
                             f"'{zipfile_path}'!\nMembers:{ambig}")
        else:
            raise ValueError(f"Pattern: '{member_pattern}' matches no members"
                             f" of '{zipfile_path}'!")

    def neighbor(self, member_pattern: str) -> Self:
        """
        Access to another item in the Archive File

        Parameters
        ----------
        member_pattern : str
            Full match string for accessing another member.

        Returns
        -------
        Self
            Another instance of the class.

        """
        return ZipItem(self.zipfile_path, member_pattern=member_pattern)

    def __getitem__(self, item: str) -> Self:
        """
        Indexing for `neighbor` method

        """
        return self.neighbor(item)

    def _ipython_key_completions_(self) -> list[str]:
        return self.keys()

    def keys(self) -> list[str]:
        """
        Access to list of neighbors

        """
        return self.get_member_names()

    def __repr__(self) -> str:
        return (f"ZipItem(zipfile_path={self.zipfile_path},"
                f" member_pattern={re.escape(self.member_name)})")

    def __str__(self) -> str:
        return self.member_name

    def open(self) -> os.PathLike:
        """
        Opens the internal file to be in binary read.


        Returns
        -------
        os.PathLike
            Binary open mode access to internal file.

        """
        self.zf = self.compression_class(self.zipfile_path)
        _, _, access = self.get_compressed_member_keywords()
        self.fid = getattr(self.zf, access)(self.member_name)
        return self.fid

    def seek(self,
             offset: int = 0,
             whence: int = 0) -> int:
        """
        open(file, 'rb').seek(offset, whence)

        Returns
        -------
        int
            Current position in the file.

        """
        with self:
            self.__pointer = self.fid.seek(offset, whence)
        return self.__pointer

    def read(self,
             n: int = None,
             decode: bool = False) -> bytes:
        """
        open(file, 'rb').read(n)

        Returns
        -------
        out : bytes
            Bytes from current position to n-bytes after.

        """
        with self:
            self.fid.seek(self.__pointer)
            out = self.fid.read(n)
            self.__pointer = self.fid.tell()
        return out.decode() if decode else out

    def tell(self):
        """
        Tells the current file pointerS

        """
        return self.__pointer

    def extract(self, destination_directory: str) -> str:
        """
        Direct access to extracting a file

        Parameters
        ----------
        destination_directory : str
            Destination for extraction.

        """
        os.makedirs(destination_directory, exist_ok=True)
        member = os.path.basename(self.member_name)
        file = os.path.join(destination_directory, member)
        current_pointer = self.__pointer
        self.seek(0,0)
        with open(file, 'wb') as fid:
            fid.write(self.read())
        self.seek(current_pointer, 0)
        return file


    def close(self) -> None:
        """
        Releases file hooks.

        """
        self.fid.close()
        self.zf.close()
        
        self.fid = None
        self.zf = None

    @property
    def suffix(self) -> str:
        """
        File extension of internal file

        """
        _, ext = os.path.splitext(self.member_name)
        return ext

    def __enter__(self) -> os.PathLike:
        return self.open()

    def __exit__(self, etype, e, tb) -> None:
        return self.close()

    @HybridMethod('zipfile_path')
    def get_compression_class(self,
                              zipfile_path: str = None):
        """
        Returns the python type of the reader that should be used to open
        the selected file.

        Parameters
        ----------
        self : type(Self) | Self
            Class or Instance.
        zipfile_path : str
            Path to the file.

        Returns
        -------
        compression_class : type
            File object type to open the zipfile with.

        """
        compression_class = None
        if zipfile.is_zipfile(zipfile_path):
            compression_class = zipfile.ZipFile
        elif tarfile.is_tarfile(zipfile_path):
            compression_class = tarfile.TarFile
        if not compression_class:
            raise NotImplementedError(
                f"No supported compression types for {zipfile_path}!")

        return compression_class

    @HybridMethod('zipfile_path')
    def get_compressed_member_keywords(self,
                                       zipfile_path: str = None) -> tuple[str]:
        """
        The different compression libraries have different attributes/methods
        used for accessing internal members

        Parameters
        ----------
        self : type(Self) | Self
            Class or Instance.
        zipfile_path : str
            Path to the file.


        Returns
        -------
        members : tuple[str]
            iternames method name, getmember name, and read name.

        """
        members = "", "", ""
        if zipfile.is_zipfile(zipfile_path):
            members = "namelist", "getinfo", "open"
        elif tarfile.is_tarfile(zipfile_path):
            members = "getnames", "getmember", "extractfile"

        if not members:
            raise NotImplementedError(
                f"No supported compression types for {zipfile_path}!")

        return members

    @HybridMethod('zipfile_path')
    def get_member_names(self, zipfile_path: str = None) -> list[str]:
        """
        Retrieves the names of all members in the zipfile

        Parameters
        ----------
        self : type(Self) | Self
            Class or Instance.
        zipfile_path : str
            Path to the file.

        Returns
        -------
        list
            Names of files (not directories) in the archive.

        """
        (iternames_kwd,
         _,
         _) = self.get_compressed_member_keywords(zipfile_path)
        compression_class = self.get_compression_class(zipfile_path)

        with compression_class(zipfile_path) as cf:
            members = getattr(cf, iternames_kwd)()
        return [member for i, member in enumerate(members)
                if not any(m.startswith(member) for m in members[i+1:])]

    @HybridMethod('zipfile_path', 'member_name')
    def get_member(self,
                   zipfile_path: str = None,
                   member_name: str = None) -> zipfile.ZipInfo | tarfile.TarInfo:
        """
        Info class retrieval for a member in the archive.

        Parameters
        ----------
        self : type(Self) | Self
            Class or Instance.
        zipfile_path : str
            Path to the file.
        member_name : str
            Explicit member name to retrieve.

        Returns
        -------
        member : zipfile.ZipInfo|tarfile.TarInfo
            Info class from the appropriate package.

        """
        archive_type = self.get_compression_class(zipfile_path)
        _, member, _ = self.get_compressed_member_keywords(zipfile_path)
        with archive_type(zipfile_path) as zf:
            member = getattr(zf, member)(member_name)
        return member

    @classmethod
    def factory(cls,
                zipfile_path: str,
                *,
                pattern: str = None,
                categories: dict[str, dict[bytes, int]] = None,
                extensions: Iterable[str] = None) -> dict[str, Self | list[Self]]:
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
        for member_name in cls.get_member_names(zipfile_path):
            if member_name.endswith("/"):
                continue
            if pattern and not re.match(pattern, member_name):
                continue
            if extensions and os.path.splitext(member_name)[1] not in extensions:
                continue
            item = cls(zipfile_path, re.escape(member_name))
            if not categories:
                output[member_name] = item
                continue
            for category, definition in categories.items():
                matched = True
                with item.open() as fid:
                    for condition, position in definition.items():
                        if isinstance(condition, str):
                            condition = condition.encode()
                        fid.seek(position, 0)
                        b = fid.read(len(condition) or None)
                        matched &= (b == condition)
                if matched:
                    if category not in output:
                        output[category] = []
                    output[category].append(item)
        return output
