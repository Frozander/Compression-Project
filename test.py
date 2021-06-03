from compressor import FrozCompressor
import difflib

file_name = "test.txt"


def main():

    compressor = FrozCompressor()
    compressor.read_file(file_name, job_count=4)
    compressor.write_to_file('lossless.froz')

    # CORRUPT FILE
    # f = open("lossless.froz", "rb+")
    # f.seek(0)
    # f.write(b'123456789')
    # f.close()

    compressor.read_file('lossless.froz')
    compressor.write_to_file("out.txt")

    # Compare outputs
    with open(file_name, "r") as f:
        original_data = f.read().strip().splitlines()
    with open("out.txt", "r") as f:
        decoded_data = f.read().strip().splitlines()

    print("Diff between original data and decoded data:")
    for line in difflib.unified_diff(original_data, decoded_data, fromfile=file_name, tofile='out.txt', lineterm='', n=0):
        print(line)


if __name__ == "__main__":
    main()
