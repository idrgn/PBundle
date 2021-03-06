import os
import zlib
from pathlib import Path

from const import BND_FILE_HEADER, BND_HEADER, GZIP_HEADER
from data import *


class cc:
    """
    TODO: What is this?
    """
    def __init__(self, bnd_file):
        self.bnd_file = bnd_file


class Entry:
    """
    Represents a BND file entry
    TODO: BND file entries should also be BND
    """
    def __init__(self, identifier, crc, aaddr, daddr, size, flevel, length, prlen, cbaddr, file_name, fdata):
        self.identifier = identifier
        self.crc = crc
        self.aaddr = aaddr
        self.daddr = daddr
        self.size = size
        self.flevel = flevel
        self.length = length
        self.prlen = prlen
        self.cbaddr = cbaddr
        self.fname = file_name
        self.fdata = fdata


class BND:
    """
    Represents a BND file
    """
    def __init__(self):
        self.version = 0
        self.info = 0
        self.file = 0
        self.entries = 0
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
            while read > initial or read <= (-1 - initial):
                self.extract_entry(index, path)
                index += 1
                if index > len(self.data)-1:
                    return
                read = self.data[index].flevel
        else:
            self.extract_entry(index, path)

    def extract_entry(self, index, npath):
        if self.data[index].flevel > 0:
            return
        path = self.get_path(index)
        lpath = path.split("/")
        if npath == "":
            currpath = os.path.dirname((os.path.abspath(
                self.path))) + os.sep + "extracted" + os.sep + os.path.basename(self.path) + os.sep
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
        if index + movement > len(self.data) - 1 or index + movement < 0:
            return -1
        if self.data[index].flevel != self.data[index+movement].flevel:
            return -1
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
            self.data.insert(insertion, Entry(-1, 0x0, 0x0, 0x0, len(data),
                             position, 0x0, 0x0, 0x0, Path(filename).name.lower(), data))
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
        self.data.insert(insertion, Entry(0, 0x0, 0x0, 0x0, 0x0,
                         position, 0x0, 0x0, 0x0, filename.lower(), b''))
        self.update_identifiers()
        self.update_crc()
        return insertion

    def get_parent(self, entry):
        # print("Looking for parent of: ", entry)
        old = self.data[entry].flevel
        if old == -1 or old == 0:
            return 0
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
        if current == -1 or current == 1:
            return self.data[entry].fname
        else:
            target = 1
        # print("Initialized, current is: ", current, "and highest is: ", highest, "target is: ", target)
        while current != target:
            # print("Current: ", current)
            if current > 0 and current < highest:
                path.insert(0, self.data[entry].fname)
                highest = current
                # print("New high: ", highest)
            entry -= 1
            if entry > len(self.data) - 1 or entry < 0:
                return "None"
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
            while read > initial or read <= (-1 - initial):
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
        """
        Counts all the files, excluding folders
        """
        counter = 0
        for i in self.data:
            if i.flevel < 0:
                counter += 1
        return counter

    def read_from_file(self, path, encrypted):
        """
        Reads data from a .bnd file
        """

        with open(path, "r+b") as f:
            data = f.read()

            # Decrypt if needed
            if encrypted:
                data = p3hash(data, "d")

            # Gzipped files
            is_gzipped = False
            is_single_bnd_file = False

            # Checks if the header is a gzip header
            if read_byte_array(data, 0x0, 0x3) == GZIP_HEADER:

                # Reassign data with the decrompressed file
                data = zlib.decompress(data, 15 + 32)
                is_gzipped = True

                # Check if the resulting file is a BND
                if read_byte_array(data, 0x0, 0x4) != BND_HEADER:

                    # Add the simple BND header to the file
                    data = BND_FILE_HEADER + data
                    is_single_bnd_file = True

            # If header is BND
            if read_byte_array(data, 0x0, 0x4) == BND_HEADER:

                # Read all the header values
                self.path = path
                self.version = read_integer(data, 0x04, 0x1)
                self.value1 = read_integer(data, 0x08, 0x1)
                self.value2 = read_integer(data, 0x0C, 0x1)
                self.info = read_integer(data, 0x10, 0x4)
                self.file = read_integer(data, 0x14, 0x4)
                self.entries = read_integer(data, 0x24, 0x4)
                self.data = []

                # Checks all the empty blocks
                check = b'\x00'*0x10
                empty_blocks = 0

                while check == b'\x00'*0x10:
                    check = read_byte_array(
                        data, 0x28 + empty_blocks * 0x10, 0x10)
                    if check == b'\x00'*0x10:
                        empty_blocks += 1

                self.entries -= empty_blocks
                self.empty_blocks = empty_blocks

                # Start reading the data
                offset = 0x0

                for i in range(self.entries):

                    crc_pointer = read_integer(data, self.info + offset + 0x3, 0x4)

                    if crc_pointer != 0:

                        # Reads CRC block containing data
                        crc_block = read_byte_array(data, crc_pointer, 0x10)

                        # Reading data from the CRC block
                        file_crc = read_integer(crc_block, 0x0, 0x4) # CRC
                        pointer_attributes = read_integer(crc_block, 0x4, 0x4) # Address to extra attributes
                        pointer_data = read_integer(crc_block, 0x8, 0x4) # Address to the start of the data
                        file_size = read_integer(crc_block, 0xC, 0x4)  # Size of the data

                        # For DATAMS: File sizes are +0x20000000
                        if file_size >= 0x20000000:
                            file_size -= 0x20000000

                        # Level of the current file (inside folders)
                        file_level = to_signed(read_integer(data, pointer_attributes, 0x1), 1)
                        # Length of the previous data block?
                        length_previous_data_block = read_integer(data, pointer_attributes + 0x1, 0x1)
                        # Length of the current data block?
                        length_current_data_block = to_signed(read_integer(data, pointer_attributes + 0x2, 0x1), 1)
                        # Pointer to CRC Block
                        pointer_crc_block = read_integer(data, pointer_attributes + 0x3, 0x4)
                        # Filename
                        file_name = read_string(data, pointer_attributes + 0x7)

                        # Read file data
                        file_data = read_byte_array(data, pointer_data, file_size)  # File data

                        # Add file
                        self.data.append(Entry
                            (i, 
                            file_crc, 
                            pointer_attributes, 
                            pointer_data, file_size, 
                            file_level, 
                            length_previous_data_block, 
                            length_current_data_block, 
                            pointer_crc_block, 
                            file_name, 
                            file_data)
                        )

                        # Add offset
                        offset += 7 + len(file_name) + 1
                        
                return 0, is_gzipped, is_single_bnd_file
            else:
                return 1, False, False

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
        """
        Saves file
        """
        if self.path != "":
            self.update_crc()

            #  === SECTION: HEADER
            file = BND_HEADER  # 0x0
            file += self.version.to_bytes(4, "little", signed=False)  # 0x4
            file += self.value1.to_bytes(4, "little", signed=False)  # 0x8
            file += self.value2.to_bytes(4, "little", signed=False)  # 0xC
            file += (0x28 + self.empty_blocks*0x10 + len(self.data) * 0x10).to_bytes(4, "little", signed=False)  # 0x10

            # files = address where files start
            file += self.info.to_bytes(4, "little", signed=False)
            file += b'\x00' * 4 * 2
            # files = amount of files with value less than zero
            file += self.count_files().to_bytes(4, "little", signed=False)
            file += (len(self.data)+self.empty_blocks).to_bytes(4, "little", signed=False)  # entries = amount of entries
            file += b'\x00' * 0x10 * self.empty_blocks

            # === SECTION: CRC BLOCKS
            # Creates a CRC list, containing all the CRC Blocks
            crc_list = []

            # Iterate over every file
            for entry in self.data:
                crc_list.append([
                    entry.crc, 
                    entry.crc.to_bytes(4, "little", signed=False), 
                    entry.aaddr.to_bytes(4, "little", signed=False), 
                    entry.daddr.to_bytes(4, "little", signed=False), 
                    entry.size.to_bytes(4, "little", signed=False)
                    ])

            # Sort
            crc_list.sort()
            
            # Write in order to file
            for item in crc_list:
                file += item[1]
                file += item[2]
                file += item[3]
                file += item[4]


            # === SECTION: EXTRA DATA
            leng = 255
            data_address = 0
            data_address_list = []
            for entry in self.data:
                index = 0

                # Gets first crc of crc list
                newcrc = crc_list[0][0]

                # Finds CRC in CRC list
                while entry.crc != newcrc and index+1 < len(crc_list):
                    index += 1
                    newcrc = crc_list[index][0]

                # Calculates address of extra_data
                address = index * 0x10 + 0x28 + 0x10 * self.empty_blocks

                # Appends the data address to the list
                data_address_list.append([data_address, address])
                data_address += len(entry.fdata)

                # Add base 4 to length
                if len(entry.fdata) % 4 != 0:
                    data_address += 4 - (len(entry.fdata) % 4)

                file = replace_byte_array(file, address + 0x4, len(file).to_bytes(4, "little", signed=False))
                file += entry.flevel.to_bytes(1, "little", signed=True)
                file += leng.to_bytes(1, "little", signed=False)
                leng = 7 + len(entry.fname) + 1
                file += leng.to_bytes(1, "little", signed=False)
                file += address.to_bytes(4, "little", signed=False)
                file += str.encode(entry.fname)
                file += b'\x00'
        
            # File must end in 512
            while len(file) % 512 != 0:
                file += b'\x00'
            
            file = replace_byte_array(file, 0x14, len(file).to_bytes(4, "little", signed=False))
            base = len(file)


            # Replace addresses?
            for i in range(len(data_address_list)):
                file = replace_byte_array(file, data_address_list[i][1]+0x8, (base + data_address_list[i][0]).to_bytes(4, "little", signed=False))


            # Write the file data
            file = bytearray(file)
            # Iterate over all addresses
            for i in range(len(data_address_list)):
                # Also grabbing files from data by index
                file += self.data[i].fdata
                # Make it so next file always start on 0x4 multiple
                while len(file) % 4 != 0:
                    file += b'\x00'
            # Convert back to bytes
            file = bytes(file)

            # Create backup
            if not backup:
                if os.path.isfile(self.path + ".bak"):
                    os.remove(self.path + ".bak")
                os.rename(self.path, self.path + ".bak")
            
            # Encrypt
            if encrypted:
                file = p3hash(file, "e")
            
            # Save file
            with open(self.path, "wb") as r:
                r.write(file)
