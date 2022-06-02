import os

from data import resource_path

BND_HEADER = b'BND\x00'
GZIP_HEADER = b'\x1f\x8b\x08'

bnd_header_file = open(resource_path("res" + os.sep + "bnd_header.bin"), "r+b")
BND_FILE_HEADER = bnd_header_file.read()
bnd_header_file.close()

