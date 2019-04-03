"""
Module for JAR manifest.
"""

import os

from collections import OrderedDict
from six import BytesIO

manifest_line_length = 70


class ManifestKeyException(Exception):

    pass


class ManifestSection:

    primary_key = "Manifest-Version"

    def __init__(self, name=None):
        self.dict = OrderedDict([])
        self.dict[self.primary_key] = name

    def store(self, stream, linesep=os.linesep):

        for k, v in self.dict.items():
            write_key_val(stream, k, v, linesep)

        stream.write(linesep.encode('utf-8'))

    def get_data(self, linesep=os.linesep):

        stream = BytesIO()
        self.store(stream, linesep)
        return stream.getvalue()

    def clear(self):
        self.dict.clear()


class Manifest:
    """
    Represents a Java Manifest as an ordered dictionary containing
    the key:value pairs from the main section of the manifest, and
    zero or more sub-dictionaries of key:value pairs representing the
    sections following the main section.
    """

    def __init__(self, version="1.0", linesep=None):
        self.mf_section = ManifestSection(version)
        self.sub_sections = OrderedDict([])
        self.linesep = linesep

    def store(self, stream, linesep=None):
        """
        Serialize the Manifest to a binary stream
        """

        linesep = linesep or self.linesep or os.linesep

        self.mf_section.store(stream, linesep)
        for sect in sorted(self.sub_sections.values()):
            sect.store(stream, linesep)

    def get_data(self, linesep=None):
        """
        Serialize the entire manifest and return it as bytes
        :return bytes
        """

        # either specified here, specified on the instance, or the OS default
        linesep = linesep or self.linesep or os.linesep

        stream = BytesIO()
        self.store(stream, linesep)
        return stream.getvalue()

    def clear(self):
        """
        removes all items from this manifest, and clears and removes all
        sub-sections
        """

        for sub in self.sub_sections.values():
            sub.clear()
        self.sub_sections.clear()

        self.mf_section.clear()

    def __del__(self):
        self.clear()


def write_key_val(stream, key, val, linesep=os.linesep):
    """
    The MANIFEST specification limits the width of individual lines to
    72 bytes (including the terminating newlines). Any key and value
    pair that would be longer must be split up over multiple
    continuing lines
    :type key, val: str in Py3, str or unicode in Py2
    :type stream: binary
    """

    key = key.encode('utf-8') or ""
    val = val.encode('utf-8') or ""
    linesep = linesep.encode('utf-8')

    # check key's length
    if not (0 < len(key) < manifest_line_length - 1):
        raise ManifestKeyException("bad key length", key)

    if len(key) + len(val) > manifest_line_length - 2:
        kv_buffer = BytesIO(b": ".join((key, val)))

        # first grab 70 (which is 72 after the trailing newline)
        stream.write(kv_buffer.read(manifest_line_length))

        # now only 69 at a time, because we need a leading space and a
        # trailing \n
        part = kv_buffer.read(manifest_line_length - 1)
        while part:
            stream.write(linesep + b" ")
            stream.write(part)
            part = kv_buffer.read(manifest_line_length - 1)
        kv_buffer.close()

    else:
        stream.write(key)
        stream.write(b": ")
        stream.write(val)

    stream.write(linesep)

#
# The end.