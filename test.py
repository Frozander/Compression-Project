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
            compressor.read_file(file, job_count=2)
            compressor.write_to_file('lossless.froz')
            # compressor.write_to_file('lossless_corrupt.froz')

            # CORRUPT FILE (This part can be used to corrupt files)
            # f = open("lossless_corrupt.froz", "rb+")
            # f.seek(0)
            # f.write(b'1234567890')
            # f.close()

            # compressor.read_file('lossless_corrupt.froz')
            # compressor.write_to_file("out_corrupt.txt")

            compressor = FrozCompressor()
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

            # Compare outputs
            with open(file, "r") as f:
                original_data = f.read().strip().splitlines()
            with open("out.txt", "r") as f:
                decoded_data = f.read().strip().splitlines()

            print("Diff between original data and decoded data:")
            for line in difflib.unified_diff(original_data, decoded_data, fromfile=file, tofile='out.txt', lineterm='', n=0):
                print(line)

            print()


if __name__ == "__main__":
    main()
