import re
import sys
import os

def convert_dump_to_hex(input_file_path):
    # 正規表現パターン: アドレス、命令コードをマッチさせる
    pattern = re.compile(r'^\s*([0-9a-f]+):\s*([0-9a-f]+)\s+')

    # 出力ファイル名の生成: *dump を *hex に置き換え
    output_file_path = input_file_path.replace('dump', 'hex')

    with open(input_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
        for line in infile:
            match = pattern.match(line)
            if match:
                pc = match.group(1)          # プログラムカウンタの値
                instruction = match.group(2) # 命令コード
                # PC値と命令コードをファイルに書き出す
                outfile.write(f"0x{pc} {instruction}\n")

def convert_all_dumps_in_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".dump"):
                full_path = os.path.join(root, file)
                print(f"Converting {full_path} to HEX...")
                convert_dump_to_hex(full_path)
                print(f"Conversion complete for {full_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python convert_all_dumps.py <directory>")
        sys.exit(1)

    directory_path = sys.argv[1]
    convert_all_dumps_in_directory(directory_path)
