import os
import sys
import tempfile
from pathlib import Path
from struct import unpack
from subprocess import check_output


def p3hash(data: bytes, mode: str):
    with tempfile.NamedTemporaryFile(mode="w+b", suffix=".bin", delete=False) as tf:
        temp = Path(tf.name)
        tf.write(data)
        check_output(
            f"{resource_path('res/ext/p3h.exe').as_posix()} {tf.name} {tf.name}1 {mode}",
            shell=True,
        )
        tmp_path = Path(f"{tf.name}1")
        with open(tmp_path, "rb") as tf2:
            data = tf2.read()
        tmp_path.unlink()
    temp.unlink()
    return data


def resource_path(relative_path: str) -> Path:
    current_path = Path(".")
    if hasattr(sys, "_MEIPASS"):
        current_path = Path(sys._MEIPASS)
    else:
        current_path = Path(os.path.dirname(__file__))
    return current_path.joinpath(relative_path)


def replace_byte_array(fdata: bytes, position: int, value: bytes):
    fdata = bytearray(fdata)
    for i in range(0, len(value)):
        fdata[position + i] = value[i]
    fdata = bytes(fdata)
    return fdata


def read_uint(fdata: bytes, position: int) -> int:
    return unpack("I", read_byte_array(fdata, position, 4))[0]


def read_ushort(fdata: bytes, position: int) -> int:
    return unpack("H", read_byte_array(fdata, position, 2))[0]


def read_uchar(fdata: bytes, position: int) -> int:
    return unpack("B", read_byte_array(fdata, position, 1))[0]


def read_int(fdata: bytes, position: int) -> int:
    return unpack("i", read_byte_array(fdata, position, 4))[0]


def read_short(fdata: bytes, position: int) -> int:
    return unpack("h", read_byte_array(fdata, position, 2))[0]


def read_char(fdata: bytes, position: int) -> int:
    return unpack("b", read_byte_array(fdata, position, 1))[0]


def read_byte_array(fdata: bytes, position: int, size: int) -> bytes:
    if position + size > len(fdata):
        size = len(fdata) - position
    return fdata[position : position + size]


# def read_str(fdata: bytes, position: int) -> str:
#     string = ""
#     offset = 0x0
#     while read_byte_array(fdata, position + offset, 0x1) != b"\x00":
#         string += chr(read_uchar(fdata, position + offset))
#         offset += 1
#     return string


def read_str(fdata: bytes, position: int) -> str:
    string_bytes = bytearray()
    offset = 0x0
    while (last_byte := read_uchar(fdata, position + offset)) != 0x00:
        string_bytes.append(last_byte)
        offset += 1
    string = unpack(f"{len(string_bytes)}s", string_bytes)[0].decode()
    return string


def sizeof_fmt(num, suffix: str = "B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)
