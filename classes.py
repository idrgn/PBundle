from data import *
import zlib
import os
from pathlib import Path
import numpy as np

class cc:
    def __init__(self, bnd_file):
        self.bnd_file = bnd_file

class Entry:
    def __init__(self, identifier, crc, aaddr, daddr, size, flevel, length, prlen, cbaddr, fname, fdata):
        self.identifier = identifier
        self.crc = crc
        self.aaddr = aaddr
        self.daddr = daddr
        self.size = size
        self.flevel = flevel
        self.length = length
        self.prlen = prlen
        self.cbaddr = cbaddr
        self.fname = fname
        self.fdata = fdata

class BND:
    def __init__(self):
        self.version = 0
        self.info = 0
        self.file = 0
        self.entries =  0
        self.data = []
        self.empty_blocks = 0
        self.value1 = 0
        self.value2 = 0
        self.path = ""
        self.ext_data_path = ""

    def extract_handler(self, index, path):
        if self.data[index].flevel > 0:
            initial = self.data[index].flevel
            index += 1
            if index > len(self.data)-1:
                return
            read = self.data[index].flevel
            while read > initial or read <= (-1 -initial):
                self.extract_entry(index, path)
                index += 1
                if index > len(self.data)-1:
                    return
                read = self.data[index].flevel
        else: self.extract_entry(index, path)

    def extract_entry(self, index, npath):
        if self.data[index].flevel > 0: return
        path = self.get_path(index)
        lpath = path.split("/")
        if npath == "":
            currpath = os.path.dirname((os.path.abspath(self.path))) + os.sep + "extracted" + os.sep + os.path.basename(self.path) + os.sep
        else:
            currpath = npath.replace("/", os.sep)
            currpath = currpath.replace("\\", os.sep)
        for i in lpath[:-1]:
            currpath += i + os.sep
        try:
            os.makedirs(currpath)
        except OSError:
            pass
        with open(currpath + lpath[-1], "wb") as r:
            r.write(self.data[index].fdata)

    def move_entry(self, index, movement):
        if index + movement > len(self.data) - 1 or index + movement < 0 : return -1
        if self.data[index].flevel != self.data[index+movement].flevel: return -1
        temp = self.data[index]
        self.data[index] = self.data[index + movement]
        self.data[index + movement] = temp 
        return index + movement

    def replace_entry_data(self, index, filename):
        with open(filename, "r+b") as f:
            data = f.read()
            self.data[index].fdata = data
            self.data[index].size = len(data)

    def replace_entry_send_data(self, index, data):
        self.data[index].fdata = data
        self.data[index].size = len(data)

    def update_identifiers(self):
        index = 0
        for i in self.data:
            i.identifier = index
            index += 1

    def add_entry(self, index, filename):
        with open(filename, "r+b") as f:
            data = f.read()
            if index == -1:
                insertion = 0
                position = -1
            elif self.data[index].flevel == -1:
                insertion = 0
                position = -1 
            elif self.data[index].flevel > 0:
                insertion = index + 1
                position = -1-self.data[index].flevel
            elif self.data[index].flevel < 0:
                insertion = self.get_parent(index) + 1
                position = self.data[index].flevel
            # print("Adding file at index: ", insertion, "of: ", len(self.data))
            self.data.insert(insertion, Entry(-1, 0x0, 0x0, 0x0, len(data), position, 0x0, 0x0, 0x0, Path(filename).name.lower(), data))
            self.update_identifiers()
            self.update_crc()
            return insertion

    def add_folder(self, index, filename):
        if index == -1:
            insertion = 0
            position = 1
        elif self.data[index].flevel == -1:
            insertion = 0
            position = 1
        elif self.data[index].flevel > 0:
            insertion = index + 1
            position = self.data[index].flevel + 1
        elif self.data[index].flevel < 0:
            insertion = self.get_parent(index) + 1
            position = self.data[self.get_parent(index)].flevel + 1
        # print("Adding file at index: ", insertion, "of: ", len(self.data))
        self.data.insert(insertion, Entry(0, 0x0, 0x0, 0x0, 0x0, position, 0x0, 0x0, 0x0, filename.lower(), b''))
        self.update_identifiers()
        self.update_crc()
        return insertion

    def get_parent(self, entry):
        # print("Looking for parent of: ", entry)
        old = self.data[entry].flevel
        if old == -1 or old == 0: return 0
        new = old
        if old > 0:
            while old == new or new < 0:
                entry -= 1
                new = self.data[entry].flevel
        else:
            while old == new:
                entry -= 1
                new = self.data[entry].flevel
        # print("Parent is: ", entry)
        return entry

    def get_path(self, entry):
        path = []
        filename = self.data[entry].fname
        current = self.data[entry].flevel
        if current < 0:
            highest = abs(current)
        else:
            highest = current
        if current == -1 or current == 1: return self.data[entry].fname
        else: target = 1
        # print("Initialized, current is: ", current, "and highest is: ", highest, "target is: ", target)
        while current != target:
            # print("Current: ", current)
            if current > 0 and current < highest:
                path.insert(0, self.data[entry].fname)
                highest = current
                # print("New high: ", highest)
            entry -= 1
            if entry > len(self.data) - 1 or entry < 0: return "None"
            current = self.data[entry].flevel
        path.insert(0, self.data[entry].fname) 
        return "".join(path) + filename

    def delete_entry(self, entry):
        if self.data[entry].flevel > 0:
            initial = self.data[entry].flevel
            self.data.pop(entry)
            if entry > len(self.data)-1:
                return
            read = self.data[entry].flevel
            while read > initial or read <= (-1 -initial):
                # print("Deleting: ", self.data[entry].flevel)
                # print(entry, len(self.data))
                self.data.pop(entry)
                if entry > len(self.data)-1:
                    return
                read = self.data[entry].flevel
        else:
            self.data.pop(entry)
        self.update_identifiers()
        self.update_crc()

    def update_crc(self):
        path = []
        current_depth = 0
        filename = ""
        for i in self.data:
            if i.flevel < 0:
                filename = "".join(path)+i.fname
            else:
                if i.flevel > current_depth:
                    path.append(i.fname)
                else:
                    if (current_depth-i.flevel) != 0:
                        path = path[:-(current_depth-i.flevel)]
                        current_depth = i.flevel
                if i.flevel == current_depth:
                    path[i.flevel-1] = i.fname
                current_depth = i.flevel
                filename = "".join(path)
            i.crc = zlib.crc32(str.encode(filename))

    def count_files(self):
        counter = 0
        for i in self.data:
            if i.flevel < 0: counter += 1
        return counter

    def read_from_file(self, path, encrypted):
        
        with open(path, "r+b") as f:

            data = f.read()

            if encrypted:

                data = p3hash(data, "d")

            gzpd = False
            sing = False

            if read_byte_array(data, 0x0, 0x3) == b'\x1f\x8b\x08':

                data = zlib.decompress(data, 15 + 32)
                gzpd = True

                if read_byte_array(data, 0x0, 0x4) != b'BND\x00':

                    x = open(resource_path("gzipped_file.bin"), "r+b")
                    ndata = x.read()
                    data = ndata + data
                    sing = True

            if read_byte_array(data, 0x0, 0x4) == b'BND\x00':

                # print("Processing BND file:", path)

                self.path = path
                self.version = read_integer(data, 0x04, 0x1)
                self.value1 = read_integer(data, 0x08, 0x1)
                self.value2 = read_integer(data, 0x0C, 0x1)
                self.info = read_integer(data, 0x10, 0x4)
                self.file = read_integer(data, 0x14, 0x4)
                self.entries = read_integer(data, 0x24, 0x4)
                self.data = []

                check = b'\x00'*0x10
                empty_blocks = 0

                while check == b'\x00'*0x10:
                    check = read_byte_array(data, 0x28 + empty_blocks * 0x10, 0x10)
                    if check == b'\x00'*0x10: 
                        empty_blocks += 1

                # print("Empty blocks: ", empty_blocks)
                
                self.entries -= empty_blocks;

                self.empty_blocks = empty_blocks

                offset = 0x0

                for i in range(self.entries):
                    
                    p_crc = read_integer(data, self.info + offset + 0x3, 0x4)
                    
                    if p_crc != 0:
                        
                        crc_block = read_byte_array(data, p_crc, 0x10)

                        # CRC BLOCK 
                        
                        f_crc = read_integer(crc_block, 0x0, 0x4) # CRC of the file
                        f_aaddr = read_integer(crc_block, 0x4, 0x4) # Address to extra attributes
                        f_daddr = read_integer(crc_block, 0x8, 0x4) # Address to the start of the data
                        f_size = read_integer(crc_block, 0xC, 0x4) # Size of the data

                        if f_size >= 0x20000000: f_size -= 0x20000000

                        # DATA BLOCK

                        flevel = to_signed(read_integer(data, f_aaddr, 0x1), 1) # Level of the current file (inside folders)
                        length = read_integer(data, f_aaddr + 0x1, 0x1) # Length of the previous data block   

                        prlen = to_signed(read_integer(data, f_aaddr + 0x2, 0x1), 1) # Length of the current data block   
                        cbaddr = read_integer(data, f_aaddr + 0x3, 0x4) # Pointer to CRC Block
                        
                        fname = read_string(data, f_aaddr + 0x7)

                        # READ FILE DATA
                        
                        fdata = read_byte_array(data, f_daddr, f_size) # File data

                        # print("\nFile: ", i, "\nLevel:", flevel, "\nName: ", fname, "\nSize: ", hex(len(fdata)), "\nCRC:  ", hex(f_crc), "\nPrlen:", prlen)

                        self.data.append(Entry(i, f_crc, f_aaddr, f_daddr, f_size, flevel, length, prlen, cbaddr, fname, fdata))

                        offset += 7 + len(fname) + 1
                        
                return  0, gzpd, sing

            else: return 1, False, False

    def print_all_entries(self):
        print(" ==== ALL ENTRIES:")
        for i in self.data:
            print("\n")
            print("File", i.identifier)
            print("CRC: ", hex(i.crc))
            print("Porperty addr: ", hex(i.aaddr))
            print("Data addr: ", hex(i.daddr))
            print("File size: ", hex(i.size))
            print("Level: ", i.flevel)
            print("Entry length: ", i.length)
            print("Previous length: ", i.prlen)
            print("CRC addr: ", hex(i.cbaddr))
            print("Filename: ", i.fname)

    def return_all_entries(self):
        return self.data

    def save_file(self, encrypted, backup):
        if self.path != "":
            self.update_crc()
            new_file = b'BND\x00' # 0x0
            new_file += self.version.to_bytes(4, "little", signed = False) #0x4
            new_file += self.value1.to_bytes(4, "little", signed = False) #0x8
            new_file += self.value2.to_bytes(4, "little", signed = False) #0xC
            # new_file += b'\x00' * 4 * 2 # 0x8 - 0xC
            new_file += (0x28 + self.empty_blocks*0x10 + len(self.data)*0x10).to_bytes(4, "little", signed = False) # 0x10
            new_file += self.info.to_bytes(4, "little", signed = False) # files = address where files start
            new_file += b'\x00' * 4 * 2
            new_file += self.count_files().to_bytes(4, "little", signed = False) # files = amount of files with value less than zero
            new_file += (len(self.data)+self.empty_blocks).to_bytes(4, "little", signed = False) # entries = amount of entries
            new_file += b'\x00' * 0x10 * self.empty_blocks
            crc_list = []
            for i in self.data:
                crc_list.append([i.crc, i.crc.to_bytes(4, "little", signed = False), i.aaddr.to_bytes(4, "little", signed = False), i.daddr.to_bytes(4, "little", signed = False), i.size.to_bytes(4, "little", signed = False)])
            crc_list.sort()
            for i in crc_list:  
                new_file += i[1]
                new_file += i[2]
                new_file += i[3]
                new_file += i[4]
            leng = 255
            data_addr = 0
            data_addr_list = []
            for i in self.data:
                index = 0
                newcrc = crc_list[0][0]
                while i.crc != newcrc and index+1 < len(crc_list):
                    index += 1
                    newcrc = crc_list[index][0]
                addr = index * 0x10 + 0x28 + 0x10 * self.empty_blocks
                data_addr_list.append([data_addr, addr])
                data_addr += len(i.fdata)
                if len(i.fdata) % 4 != 0:
                    data_addr += 4 - (len(i.fdata) % 4)
                new_file = replace_byte_array(new_file, addr + 0x4, len(new_file).to_bytes(4, "little", signed = False))
                new_file += i.flevel.to_bytes(1, "little", signed = True)
                new_file += leng.to_bytes(1, "little", signed = False)
                leng = 7 + len(i.fname) + 1
                new_file += leng.to_bytes(1, "little", signed = False)
                new_file += addr.to_bytes(4, "little", signed = False)
                new_file += str.encode(i.fname)
                new_file += b'\x00'
            while len(new_file) % 512 != 0:
                new_file += b'\x00'
            new_file = replace_byte_array(new_file, 0x14, len(new_file).to_bytes(4, "little", signed = False))
            base = len(new_file)
            for i in range(len(data_addr_list)):
                new_file = replace_byte_array(new_file, data_addr_list[i][1]+0x8, (base + data_addr_list[i][0]).to_bytes(4, "little", signed = False))
            new_file = bytearray(new_file)
            for i in range(len(data_addr_list)):
                new_file += self.data[i].fdata
                while len(new_file) % 4 != 0:
                    new_file += b'\x00'
            new_file = bytes(new_file)
            if not backup:
                if os.path.isfile(self.path + ".bak"):
                    os.remove(self.path + ".bak")
                os.rename(self.path, self.path + ".bak")
            if encrypted:
                new_file = p3hash(new_file, "e")
            with open(self.path, "wb") as r:
                r.write(new_file)
