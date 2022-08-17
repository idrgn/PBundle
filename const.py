from data import resource_path

BND_HEADER = b"BND\x00"
GZIP_HEADER = b"\x1f\x8b\x08"
EMPTY_BLOCK = b"\x00" * 0x10
EMPTY_WORD = b"\x00\x00\x00\x00"
bnd_header_file = open(resource_path("res/bnd_header.bin"), "r+b")
BND_FILE_HEADER = bnd_header_file.read()
bnd_header_file.close()
