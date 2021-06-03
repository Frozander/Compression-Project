"""
froz file format, converter, compressor and explorer.

Exit file format: .froz
froz file structure:
    Dictionary_Padding Data_Padding
    Dictionary
    Data
"""
import argparse
import numpy as np
import heapq


def encode(data):
    key = {}
    encoded = ""
    corpus = {}

    for x in data:
        corpus[x] = corpus.get(x, 0) + 1

    # sort the characters in descending order
    corpus = sorted(corpus.items(), key=lambda x: x[1], reverse=True)

    tree = corpus

    while len(tree) > 1:
        left = heapq.heappop(tree)
        right = heapq.heappop(tree)

        for x in left[1]:
            key[x] = '0' + key.get(x, "")

        for x in right[1]:
            key[x] = '1' + key.get(x, "")

        heapq.heappush(tree(left[0] + right[0], left[1] + right[1]))

    for x in key:
        print(x, key[x])

    for c in data:
        encoded += key[c]

    rem = len(encoded) % 8
    key['rem'] = rem
    encoded += '0' * rem

    return encoded


# MAIN CODE
parser = argparse.ArgumentParser(
    prog="FRO Compressor",
    description="froz file format, converter, compressor and explorer.")
parser.add_argument('file_name', metavar='file', type=str,
                    help="Name of the file to be processed")
parser.add_argument('-c', '--compress', action='store_true',
                    help="If supplied, compresses the input text (default action is to decompress)")
parser.add_argument('-l', '--lossy', action='store_true',
                    help="If supplied, use lossy compresion (default action causes compression to be lossles)")
args = parser.parse_args()

print("Parsed Arguments")
print(f"file_name: {args.file_name}")
print(f"compress : {args.compress}")
print(f"lossy    : {args.lossy}")


# Read and open the file as an array
with open('test.txt', 'rb') as fd:
    file_content = fd.read()
# file_content = np.array([x for x in file_content], dtype=np.dtype('uint8'))
file_content = str(file_content)
