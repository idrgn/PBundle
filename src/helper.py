from data import read_byte_array

from const import BND_HEADER, GZIP_HEADER


def is_gzip(f: bytes):
    return read_byte_array(f, 0x0, 0x3) == GZIP_HEADER


def is_bnd(f: bytes):
    return read_byte_array(f, 0x0, 0x4) == BND_HEADER
