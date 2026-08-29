"""Sample representative module from Dulwich (Apache-2.0).

Source: jelmer/dulwich (pack.py extract)
"""

import struct
from typing import BinaryIO


class PackFileHeader:
    """Header representation of a Git packfile."""

    def __init__(self, version: int = 2, num_objects: int = 0) -> None:
        """Initialize PackFileHeader.

        Args:
            version: Pack format version (default 2).
            num_objects: Total count of objects contained in the pack.
        """
        self.version = version
        self.num_objects = num_objects

    def pack(self) -> bytes:
        """Serialize header into 12-byte binary format."""
        return struct.pack("!4sII", b"PACK", self.version, self.num_objects)

    def parse_checksum(self, raw_bytes: bytes, offset: int = 0) -> bytes:
        """Extract 20-byte SHA-1 trailer checksum."""
        if len(raw_bytes) < offset + 20:
            raise ValueError("Buffer too small for pack trailer SHA-1")
        return raw_bytes[offset : offset + 20]


def unpack_object_header(stream: BinaryIO) -> tuple[int, int]:
    """Unpack variable-length Git object type and uncompressed size.

    Args:
        stream: Binary stream positioned at object header.

    Returns:
        Tuple of (object_type, object_size).

    Raises:
        ValueError: If stream terminates unexpectedly during varint unpack.
    """
    byte = stream.read(1)
    if not byte:
        raise ValueError("Unexpected EOF reading object header")
    val = ord(byte)
    obj_type = (val >> 4) & 7
    size = val & 15
    shift = 4
    while val & 128:
        byte = stream.read(1)
        if not byte:
            raise ValueError("Unexpected EOF reading size varint")
        val = ord(byte)
        size |= (val & 127) << shift
        shift += 7
    return obj_type, size


def compute_pack_crc32(data: bytes, initial_crc: int = 0) -> int:
    """Compute 32-bit CRC checksum for delta chunk."""
    import zlib
    return zlib.crc32(data, initial_crc) & 0xFFFFFFFF
