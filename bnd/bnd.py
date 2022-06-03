import gzip
import zlib

from const import BND_FILE_HEADER, BND_HEADER, EMPTY_BLOCK, EMPTY_WORD, GZIP_HEADER
from data import p3hash, read_byte_array, read_integer, read_string, replace_byte_array, to_signed


class BND:
    """
    BND Object
    """
    def __init__(self, data: bytes = [], name: str = "", depth: int = 0, encrypted: bool = False, is_folder = False, level:int = None):
        self.file_list = []
        self.name = name
        self.depth = depth
        self.encrypted = encrypted
        self.parent = None
        self.level = level

        # Is folder
        self.is_folder = is_folder
        self.is_raw = False
        if self.is_folder: return

        # Gzipped or single BND
        self.is_gzipped = False
        self.is_single_file = False

        # Default values
        self.add_default_values()

        # Ignore DATAMS.HED
        if name == "datams.hed":
            self.is_raw = True
            self.data = data
        else:
            self.read_from_file(data)
        
        # Print data
        # self.print_data()

    def get_root_parent(self):
        """
        Gets root parent
        """
        if self.parent == None:
            return self
        else:
            return self.get_root_parent()

    def get_depth_file_list(self):
        """
        Gets file list with folders in same directory, in order
        """
        new_list = []
        for file in self.file_list:
            new_list.append(file)
            if file.is_folder:
                new_list.extend(file.get_depth_file_list())
        return new_list

    def get_all_children_bytes(self):
        """
        Returns all files as a list of byte arrays
        """
        list = []
        for item in self.file_list:
            if not item.is_folder:
                list.append(item.to_bytes())
        return list

    def add_default_values(self):
        """
        Set default values for a BND file
        """
        self.raw_data = None
        self.version = None
        self.value1 = None
        self.value2 = None
        self.info = None
        self.file = None
        self.entries = None
        self.empty_blocks = None

    def print_data(self):
        """
        Shows all the files inside the BND
        """
        print("File: " + self.name)
        for item in self.file_list:
            print(" - Files in folder " + str(item.get_full_path()) + " : " + str(item.get_file_count()))

    def get_file_count(self):
        """
        Gets the file count, including folders
        """
        count = 0
        for item in self.file_list:
            count += 1
            if item.is_folder:
                count += item.get_file_count()
        return count

    def get_total_file_count(self):
        """
        Gets the file count, including folders and sub items
        """
        count = 0
        for item in self.file_list:
            count += 1
            if not item.is_raw:
                count += item.get_total_file_count()
        return count

    def get_bnd_count(self):
        """
        Counts amount of BND files
        """
        count = 0
        for item in self.file_list:
            if not item.is_folder:
                count +=1
        return count

    def get_last_folder(self):
        """
        Obtains the last folder inside the BND
        """
        for item in reversed(self.file_list):
            if item.is_folder:
                return item
        return None

    def get_parent(self):
        """
        Add item to file list
        """
        return self.parent

    def get_full_path(self):
        """
        Return full path
        """
        name = self.name

        # If no name, add root
        if name == "": name = "root"

        # If has parent, add parent name
        if self.parent:
            name = self.parent.get_full_path() + name

        # If noit folder, add slash
        if not self.is_folder:
            name = name + "/"

        return name

    def get_local_path(self):
        """
        Return local path
        """
        if self.parent == None:
            return self.name
        else:
            if not self.parent.is_folder:
                return self.name
            else:
                return self.parent.get_local_path() + self.name

    def add_to_file_list(self, item: object):
        """
        Add item to file list
        """
        item.set_parent(self)
        self.file_list.append(item)

    def get_crc(self):
        """
        Converts full path to CRC
        """
        return zlib.crc32(str.encode(self.get_local_path()))

    def set_parent(self, parent: object):
        """
        Sets parent object
        """
        self.parent = parent

    def has_parent(self):
        """
        Returns true if object has parent
        """
        return self.parent != None

    def read_from_file(self, data):
        """
        Reads data from a .BND file
        """
        # Decrypt if needed
        if self.encrypted:
            data = p3hash(data, "d")

        # Checks if the header is a gzip header
        if read_byte_array(data, 0x0, 0x3) == GZIP_HEADER:

            # Reassign data with the decrompressed file
            data = zlib.decompress(data, 15 + 32)
            self.is_gzipped = True

            # Check if the resulting file is a BND
            if read_byte_array(data, 0x0, 0x4) != BND_HEADER:

                # Add the simple BND header to the file
                self.data = data
                data = BND_FILE_HEADER + data
                self.is_single_file = True

        # If header is BND
        if read_byte_array(data, 0x0, 0x4) == BND_HEADER:

            # Read all the header values
            self.version = read_integer(data, 0x04, 0x1)
            self.value1 = read_integer(data, 0x08, 0x1)
            self.value2 = read_integer(data, 0x0C, 0x1)
            self.info = read_integer(data, 0x10, 0x4)
            self.file = read_integer(data, 0x14, 0x4)

            # Checks all the empty blocks
            empty_blocks = 0

            check = EMPTY_BLOCK

            while check == EMPTY_BLOCK:
                check = read_byte_array(data, 0x28 + empty_blocks * 0x10, 0x10)
                if check == EMPTY_BLOCK:
                    empty_blocks += 1

            entries = read_integer(data, 0x24, 0x4) - empty_blocks

            self.empty_blocks = empty_blocks

            # Start reading the data
            offset = 0x0

            # How the file level structure will work
            # # If it increases, create a new folder and continue the loop in there
            # # If it decreases
            current_level = 0
            current_object = self

            for i in range(entries):

                crc_pointer = read_integer(data, self.info + offset + 0x3, 0x4)

                if crc_pointer != 0:
                    # Reads CRC block containing data
                    crc_block = read_byte_array(data, crc_pointer, 0x10)

                    # Reading data from the CRC block
                    pointer_attributes = read_integer(crc_block, 0x4, 0x4) # Address to extra attributes
                    pointer_data = read_integer(crc_block, 0x8, 0x4) # Address to the start of the data
                    file_size = read_integer(crc_block, 0xC, 0x4)  # Size of the data

                    # For DATAMS: File sizes are +0x20000000
                    if file_size >= 0x20000000:
                        file_size -= 0x20000000

                    # Level of the current file (inside folders)
                    file_level = to_signed(read_integer(data, pointer_attributes, 0x1), 1)

                    # Filename
                    file_name = read_string(data, pointer_attributes + 0x7)

                    # Read file data
                    file_data = read_byte_array(data, pointer_data, file_size)  # File data

                    # FILE LEVEL IS ALWAYS FOLDE RLEVEL IN NEGATIVE MINUS ONE
                    # EXAMPLE:
                    # - A file in the root directory will be level -1
                    # - A file in 2 folders will be -3

                    is_change_a_folder = False
                    processed_level = current_level

                    if (file_level < 0):
                        processed_level = abs(file_level) - 1
                    else:
                        processed_level = file_level
                        is_change_a_folder = True

                    # If unequal or new folder, do action
                    if processed_level != current_level or is_change_a_folder:

                        # If level is higher than current one, subfolder must be created
                        if processed_level > current_level:
                            # If level is root, add to root
                            new_folder = BND(None, file_name, processed_level, self.encrypted, True, level = file_level)
                            current_object.add_to_file_list(new_folder)
                            current_object = new_folder

                        # If level is lower than current one, subfolder must be exited
                        elif processed_level < current_level:
                            # Execute difference amount of times in case there is a jump
                            difference = current_level - processed_level
                            for _ in range(difference):
                                # Get parent
                                current_object = current_object.get_parent()


                        # If change is a folder, and it is in the same level as the old one
                        if (is_change_a_folder and processed_level <= current_level):
                            # Back to parent
                            current_object = current_object.get_parent()
                            # Create new folder
                            new_folder = BND(None, file_name, processed_level, self.encrypted, True, level = file_level)
                            # Set to current object
                            current_object.add_to_file_list(new_folder)
                            current_object = new_folder

                        # Set current level
                        current_level = processed_level

                    # Add file
                    if (file_level < 0):
                        current_object.add_to_file_list(BND(file_data, file_name, current_object.depth, self.encrypted, level = file_level))

                    # Add offset
                    offset += 7 + len(file_name) + 1
        
        # If not BND, raw
        else:
            self.data = data
            self.is_raw = True

    def to_bytes(self, ignore_gzip: bool = False):
        """
        Generates to_bytes object
        """
        # If raw just return own file
        if self.is_raw:
            return self.data

        # If folder return empty
        if self.is_folder:
            return b''

        # If single file
        if self.is_single_file:
            if self.is_gzipped and not ignore_gzip:
                return gzip.compress(self.data)
            else:
                return self.data



        #  === SECTION: HEADER
        file_count = self.get_file_count()
        file = BND_HEADER  # 0x0
        file += self.version.to_bytes(4, "little", signed=False)  # 0x4
        file += self.value1.to_bytes(4, "little", signed=False)  # 0x8
        file += self.value2.to_bytes(4, "little", signed=False)  # 0xC
        file += (0x28 + self.empty_blocks*0x10 + file_count * 0x10).to_bytes(4, "little", signed=False)  # 0x10

        # files = address where files start
        file += self.info.to_bytes(4, "little", signed=False)
        file += b'\x00' * 4 * 2

        # files = amount of files with value less than zero
        file += self.get_bnd_count().to_bytes(4, "little", signed=False)
        file += (file_count+self.empty_blocks).to_bytes(4, "little", signed=False)  # entries = amount of entries
        file += b'\x00' * 0x10 * self.empty_blocks



        # === SECTION: CRC LIST
        # == Generate a list with all the items inside the BND and their bytes
        formatted_list = []

        # get data of all the contained items
        file_list = self.get_depth_file_list()
        for item in file_list:
            file_bytes = item.to_bytes()

            formatted_list.append({
                "crc": item.get_crc(),
                "name": item.name,
                "size": len(file_bytes),
                "bytes": file_bytes
            })

        # reorder by crc
        formatted_list = sorted(formatted_list, key=lambda d: d["crc"]) 

        # write data: crc - empty (aaddr) - empty (daddr) - size
        for item in formatted_list:
            file += item["crc"].to_bytes(4, "little", signed=False)
            file += EMPTY_WORD
            file += EMPTY_WORD
            file += item["size"].to_bytes(4, "little", signed=False)
            


        # === SECTION: EXTRA DATA
        leng = 255
        data_address = 0
        data_address_list = []

        for entry in file_list:

            # Current file CRC
            crc = entry.get_crc()

            # First CRC of list
            newcrc = formatted_list[0]["crc"]
            index = 0

            # Finds CRC in CRC list
            while crc != newcrc and index + 1 < len(formatted_list):
                index += 1
                newcrc = formatted_list[index]["crc"]

            # Get formatted entry
            formatted_entry = formatted_list[index]

            # Calculates address of extra_data
            address = index * 0x10 + 0x28 + 0x10 * self.empty_blocks

            # Appends the data address to the list
            data_address_list.append({
                "data_address": data_address, 
                "address": address,
                "bytes": formatted_entry["bytes"]
                })
                
            data_address += formatted_entry["size"]

            # Add base 4 to length
            if formatted_entry["size"] % 4 != 0:
                data_address += 4 - (formatted_entry["size"] % 4)

            file = replace_byte_array(file, address + 0x4, len(file).to_bytes(4, "little", signed=False))
            file += entry.level.to_bytes(1, "little", signed=True)
            file += leng.to_bytes(1, "little", signed=False)
            leng = 7 + len(entry.name) + 1
            file += leng.to_bytes(1, "little", signed=False)
            file += address.to_bytes(4, "little", signed=False)
            file += str.encode(entry.name)
            file += b'\x00'
    
        # File must end in 512
        while len(file) % 512 != 0:
            file += b'\x00'
        
        file = replace_byte_array(file, 0x14, len(file).to_bytes(4, "little", signed=False))
        base = len(file)

        # Replace addresses?
        for i in range(len(data_address_list)):
            file = replace_byte_array(file, data_address_list[i]["address"]+0x8, (base + data_address_list[i]["data_address"]).to_bytes(4, "little", signed=False))

        # Write the file data
        file = bytearray(file)
        # Iterate over all addresses
        for i in range(len(data_address_list)):
            # Also grabbing files from data by index
            file += data_address_list[i]["bytes"]
            # Make it so next file always start on 0x4 multiple
            while len(file) % 4 != 0:
                file += b'\x00'
        # Convert back to bytes
        file = bytes(file)

        # Gzip
        if self.is_gzipped and not ignore_gzip:
            file = gzip.compress(file)

        # Encrypt
        if self.encrypted:
            file = p3hash(file, "e")

        # Return
        return file
