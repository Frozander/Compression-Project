from math import ceil
from os import getcwd, listdir
from compressor import FrozCompressor
import difflib
from entropy import entropy

test_tiny = "test_tiny.txt"
test_small = "test_small.txt"
test_big = "test_big.txt"
test_huge = "test_huge.txt"


def main():

    for file in listdir(getcwd()):
        if file.startswith("test_"):
            compressor = FrozCompressor()
            compressor.read_file(file, job_count=2, method='vowel_removal')
            compressor.write_to_file('lossless.froz')
            # compressor.write_to_file('lossless_corrupt.froz')

            # CORRUPT FILE
            # f = open("lossless_corrupt.froz", "rb+")
            # f.seek(0)
            # f.write(b'123456')
            # f.close()

            # compressor.read_file('lossless_corrupt.froz')
            # compressor.write_to_file("out_corrupt.txt")

            compressor.read_file('lossless.froz')
            compressor.write_to_file("out.txt")

            ent, size = entropy(file)

            print(f"File Name: {file}")
            print(f"Original File Size (bytes): {size}")
            print(f"Shannon Entropy: {ent}")
            print(
                f"Theoretical Minimum Compression (bytes): {(size * ent) / 8}")
            print(
                f"Theoretical Minimum Compression (bytes&ceil): {(size * ceil(ent)) / 8}")

            with open("lossless.froz", "rb") as fb:
                compressed = len(fb.read())
            efficiency = ((size - compressed) / ((size * ent) / 8)) * 100
            print(f"Compressed Data Size (bytes): {compressed}")
            print(f"Compression Ratio: {size / compressed}")
            print(f"Compression Efficiency: {efficiency}%")
            print()

            # Compare outputs
            # with open(test_tiny, "r") as f:
            #     original_data = f.read().strip().splitlines()
            # with open("out_corrupt.txt", "r") as f:
            #     decoded_data = f.read().strip().splitlines()

            # print("Diff between original data and decoded data:")
            # for line in difflib.unified_diff(original_data, decoded_data, fromfile=file_name, tofile='out.txt', lineterm='', n=0):
            #     print(line)


if __name__ == "__main__":
    main()
