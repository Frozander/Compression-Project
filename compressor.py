from io import BytesIO
from typing import Dict, Optional
from multiprocessing import Pool
from math import ceil
from reedsolo import RSCodec
import pickle


def bitstring_to_bytes(s):
    return int(s, 2).to_bytes((len(s) + 7) // 8, byteorder='big')


class NodeTree(object):
    '''Class for storing Huffman Code Trees'''

    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def children(self):
        return (self.left, self.right)

    def nodes(self):
        return (self.left, self.right)

    def __str__(self):
        return '%s_%s' % (self.left, self.right)


def _huffman_code_tree(node, left=True, binString=''):
    '''Creates Huffman Code Tree'''

    if type(node) is str:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(_huffman_code_tree(l, True, binString + '0'))
    d.update(_huffman_code_tree(r, False, binString + '1'))
    return d


def _generate_huffman_codes(data) -> None:
    '''Creates Huffman Code Dictionary'''

    # Calculating frequency
    freq = {}
    for c in data:
        if c in freq:
            freq[c] += 1
        else:
            freq[c] = 1

    freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    nodes = freq

    while len(nodes) > 1:
        (key1, c1) = nodes[-1]
        (key2, c2) = nodes[-2]
        nodes = nodes[:-2]
        node = NodeTree(key1, key2)
        nodes.append((node, c1 + c2))

        nodes = sorted(nodes, key=lambda x: x[1], reverse=True)

    return _huffman_code_tree(nodes[0][0])


def _encode_job(data: str, tree: Dict[str, str]) -> str:
    '''Worker function for multiproccessed encoding'''

    return ''.join([tree[c] for c in data])


def _decode_job(encoded_data: str, tree: Dict[str, str]) -> str:
    '''Worker function for multiprocessed decoding'''

    token = ""
    decoded_data = ""

    for c in encoded_data:
        token += c

        # lookup
        converted_value = tree.get(token)

        if converted_value:
            decoded_data += converted_value
            token = ""  # Reset token

    return decoded_data


def _vowel_filter(data: str) -> str:
    '''Removes vowels from input data'''

    return data.translate(str.maketrans(dict.fromkeys('aeıioöuüAEIİOÖUÜ')))


SWITCH = {
    'vowel_removal': _vowel_filter,
}


class FrozFileHandle(object):
    '''Custom file handler for handling different file extensions'''

    def __init__(self, file_name) -> None:
        self.file_name = file_name
        self.file_extension = file_name.split('.')[-1]
        self.is_compressed_by_froz = True if self.file_extension == 'froz' else False
        if self.is_compressed_by_froz:
            self.rsc = RSCodec(16)  # Fixes 8 errors or 16 erasures

    @property
    def file_data(self) -> str:
        return self.__data

    @file_data.setter
    def file_data(self, data: str) -> None:
        self.__data = data

    @property
    def huffman_code(self) -> Dict[str, str]:
        return self.__huffman_code

    @huffman_code.setter
    def huffman_code(self, tree: Dict[str, str]) -> None:
        self.__huffman_code = tree

    @property
    def padding(self) -> int:
        return self.__padding

    @padding.setter
    def padding(self, pad: int) -> None:
        self.__padding = pad

    def close(self) -> None:
        self.file_handle.close()

    def read(self, close_after: bool = True) -> None:
        if self.is_compressed_by_froz:
            self.file_handle = open(self.file_name, 'rb')

            try:
                ECC_data = self.rsc.decode(self.file_handle.read())
            except:
                print("Too many errors found, file is corrupted beyond recovery")
                # TODO: Instead of exiting, use try catch in every access to self.file_data
                print("Exiting...")
                exit(1)

            try:  # If tuple has a third element, it means there were errors detected
                if ECC_data[2]:
                    # TODO: Give more info about the errors found
                    print("File corrupted!")
                    print(
                        "Trying to fix the corruption [It might not work depending on the level of corruption]")
            except:
                pass

            ECC_buffer = BytesIO()

            ECC_buffer.write(ECC_data[0])
            ECC_buffer.seek(0)

            self.__huffman_size = int.from_bytes(
                ECC_buffer.read(4), byteorder='big')
            self.__huffman_code = pickle.loads(
                ECC_buffer.read(self.__huffman_size))
            self.__data_size = int.from_bytes(
                ECC_buffer.read(4), byteorder='big')
            self.__padding = int.from_bytes(
                ECC_buffer.read(1), byteorder='big')
            tmp = ECC_buffer.read(self.__data_size)

            # convert to binary string
            tmp = ''.join(format(byte, '08b') for byte in tmp)

            # remove padding
            tmp = tmp[0:-self.__padding]

            self.__data = [tmp]

            # print(f"self.__huffman_size: {self.__huffman_size}")
            # print(f"self.__data_size: {self.__data_size}")
            # print(f"self.__padding: {self.__padding}")
            # print(f"self.__data: {self.__data}")

        else:
            self.file_handle = open(self.file_name, 'r')
            self.__huffman_code = None
            self.__padding = None
            self.__data = self.file_handle.read()

        if close_after:
            self.close()

    def write(self, close_after: bool = True) -> None:

        if self.is_compressed_by_froz:
            self.file_handle = open(self.file_name, 'wb')
            ECC_buffer = BytesIO()

            huff_dump = pickle.dumps(self.huffman_code)
            hufn_dump = len(huff_dump).to_bytes(
                4, byteorder='big')
            padd_dump = self.padding.to_bytes(1, byteorder='big')
            data_dump = bitstring_to_bytes(''.join(self.file_data))
            size_dump = len(data_dump).to_bytes(4, byteorder='big')

            dump = [hufn_dump, huff_dump, size_dump, padd_dump, data_dump]

            ECC_buffer.writelines(dump)
            ECC_buffer.seek(0)

            rsc_data = self.rsc.encode(ECC_buffer.read())

            self.file_handle.write(rsc_data)
        else:
            self.file_handle = open(self.file_name, 'w')
            self.file_handle.write(self.file_data)

        if close_after:
            self.close()


class FrozCompressor(object):
    '''Data compressor class'''

    __slots__ = ('huffmanCode', '__data', '__encoded_data', '__decoded_data')

    def __init__(self) -> None:
        self.huffmanCode = None
        self.__data = None
        self.__encoded_data = None
        self.__decoded_data = None

    @ property
    def encoded_data(self):
        return ''.join(self.__encoded_data)

    @ property
    def decoded_data(self):
        return ''.join(self.__decoded_data)

    @ property
    def data(self):
        return self.__data

    def __reset(self) -> None:
        '''Reset class member variables. For reusing a class instance'''

        self.huffmanCode = None
        self.__data = None
        self.__encoded_data = None
        self.__decoded_data = None

    def read_file(self, file_name: str, method: Optional[str] = None, job_count: int = 1) -> None:
        '''Read a file and act depending on its extension:

        If file is a text file (.txt) loads data and encodes it

        If file is compressed by itself (.froz) loads the data and decodes it

        method: applies a lossy compression filter over the read data
        job_count: splits the encoding into specified parts. (may lower performance if the number is big relative to data size) (only works for encoding, since decoding detects part count from the .froz file)
        '''

        file = FrozFileHandle(file_name)
        file.read()
        data = file.file_data
        is_compressed = file.is_compressed_by_froz

        self.__reset()

        if is_compressed:
            self.__encoded_data = data
            self.huffmanCode = file.huffman_code
            self.decode()
        else:

            if method:
                func = SWITCH.get(method, lambda x: x)
                data = func(data)

            self.__data = data
            self.huffmanCode = _generate_huffman_codes(self.__data)
            self.encode(jobs=job_count)

    def __not_implemented_read_string(self, input: str, is_compressed: bool = False, tree: Optional[Dict[str, str]] = None):
        '''NOT IMPLEMENTED

        Read data from a string and act depending on (is_compressed)

        If (is_compressed) == False, encodes the input

        If (is_compressed) == True, decodes the input. Requires (tree) to be provided beforehand'''

        # TODO: Add behaviour for both possible string input types
        pass

    def write_to_file(self, file_name: str):

        file = FrozFileHandle(file_name=file_name)

        if file.file_extension == 'froz':  # Write compressed
            file.padding = ceil(len(self.encoded_data) / 8) * \
                8 - len(self.encoded_data)
            file.huffman_code = self.huffmanCode
            tmp = self.__encoded_data
            tmp[-1] = tmp[-1] + '0' * file.padding
            file.file_data = tmp
        else:
            file.file_data = self.decoded_data

        file.write()

    def encode(self, jobs: int = 1) -> None:
        '''Encodes data on demand.
        Doesn't need to be called if plaintext data is read through (read_string) or (read_file)'''

        # Split data
        n = len(self.__data) // jobs
        split_data = [self.__data[i: i + n]
                      for i in range(0, len(self.__data), n)]

        shards = [(shard, self.huffmanCode) for shard in split_data]
        # MP
        with Pool(jobs) as p:
            res = p.starmap_async(_encode_job, shards)
            res = res.get()

        self.__encoded_data = res

    def decode(self) -> None:
        '''Decodes data on demand.
        Doesn't need to be called if encoded data is read through (read_string) or (read_file)'''

        inv_tree = {value: key for key, value in self.huffmanCode.items()}

        shards = [(shard, inv_tree) for shard in self.__encoded_data]

        with Pool(len(self.__encoded_data)) as p:
            res = p.starmap_async(_decode_job, shards)
            res = res.get()

        self.__decoded_data = res

    def print_huffman_codes(self):
        '''Prints the huffman code'''

        print(' Char | Huffman code ')
        print('----------------------')
        for (char, value) in self.huffmanCode.items():
            print(' %-4r |%12s' % (char, value))
