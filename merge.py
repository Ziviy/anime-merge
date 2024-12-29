#!/usr/bin/python3

import os
import re
import subprocess
from joblib import Parallel, delayed
import multiprocessing
import argparse
from prettytable import PrettyTable, ALL
import threading
import time
import shutil

lock = threading.Lock()

base_filename = "CANAAN"
outputPath = "/mnt/c/tmp"
inputPath = "./"
Season = '01'

script_version = '0.2'
media_extensions = ['.mka', '.mkv', '.ass']
font_extensions = ['.ttf', '.TTF', '.Ttf', '.ttc', '.otf']
error_list = []
shema = []
base_info = ''


def output_info(number, output, file_list):
    with lock:
        os.system('clear')
        global shema, base_info
        files = ''
        for file in file_list:
            files += f'{file}\n'
        in_schema = False

        for row in shema:
            if number == row[0]:
                row[1] += f'\n{output}'
                in_schema = True

        if not in_schema:
            shema.append([number, output, files])
        table = PrettyTable(["EP", "Output", "Files"])

        for row in shema:
            table.add_row(row)

        table.align["Output"] = "l"
        table.align["Files"] = "l"
        table.sortby = "EP"
        table.hrules = ALL
        print(base_info)
        print(table)
        time.sleep(0.25)


def error_info(error):
    with lock:
        global error_list
        error_list.append(error)


def find_unique_numbers(file_list):
    print (file_list)
    numbers = set()
    for filename in file_list:
        name, extension = os.path.splitext(filename)
        if extension == '.mkv':
            digits = re.findall(r'\d+', filename)
            for digit in digits:
                numbers.add(digit.zfill(2))
    return sorted(numbers)


def font_check(file_list):
    global font_extensions
    fonts_list = []
    for filename in file_list:
        name, extension = os.path.splitext(filename)
        if extension in font_extensions:
            fonts_list.append('--add-attachment')
            fonts_list.append(os.path.join(inputPath, filename))
    return fonts_list


def group_files_by_number(file_list, number):
    grouped_files = []
    for filename in file_list:
        name, extension = os.path.splitext(filename)
        if extension in media_extensions:
            digits = re.findall(r'\d+', filename)
            for digit in digits:
                if digit.zfill(2) == number:
                    grouped_files.append(os.path.join(inputPath, filename))
    return grouped_files


def merge_files(file_list, output_filename, fonts_list, number):
    command = ['mkvmerge', '--quiet', '-o', output_filename] + file_list
    output_info(number, 'Merge: started', file_list)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        output_info(number, 'Merge: done', file_list)
        if fonts_list:
            change_font(output_filename, fonts_list, number, file_list)
    else:
        output_info(number, 'Merge: error', file_list)
        error_info(f"Merge: error\n{number}\n{stdout.decode('utf-8')}\n{stderr.decode('utf-8')}\n")


def change_font(output_filename, fonts_list, number, file_list):
    command = ['mkvpropedit', output_filename] + fonts_list
    output_info(number, 'Fonts: started', file_list)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        output_info(number, 'Fonts: done', file_list)
    else:
        output_info(number, 'Fonts: error', file_list)
        error_info(f"Fonts: error\n{number}\n{stdout.decode('utf-8')}\n{stderr.decode('utf-8')}\n")


def filte(numbers):
    filtered_numbers = [numbers[0]]
    for i in range(1, len(numbers)):
        if int(numbers[i]) - int(numbers[i - 1]) <= 5:  # dif between 2 epizodes less than  6
            filtered_numbers.append(numbers[i])
    return filtered_numbers

def move_files_to_root(input_path):
    for root, dirs, files in os.walk(input_path):
        if root == input_path:
            continue
        for file in files:
            file_path = os.path.join(root, file)
            new_path = os.path.join(input_path, file)
            try:
                # Перемещаем файл
                shutil.move(file_path, new_path)
                print(f"Moved: {file_path} -> {new_path}")
            except Exception as e:
                print(f"Error moving {file_path}: {e}")

def main():
    global base_info
    base_info += f'\
Info:\n\
    Script version: {script_version}\n\
    Media extensions: {media_extensions}\n\
    Font extensinons: {font_extensions}\n'

    move_files_to_root(inputPath)

    # Get list of files with absolute paths
    file_list = [os.path.join(inputPath, f) for f in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, f))]
    numbers = find_unique_numbers([os.path.basename(f) for f in file_list])
    fonts_list = font_check([os.path.basename(f) for f in file_list])
    num_threads = multiprocessing.cpu_count()

    numbers = filte(numbers)

    Parallel(n_jobs=num_threads, backend='threading')(
        delayed(process_number)(number, file_list, fonts_list) for number in numbers)

    fonts = '\n\t'.join(map(str, fonts_list[1::2]))
    print(f"List of added fonts:\n {fonts}")

    for error in error_list:
        print(error)


def process_number(number, file_list, fonts_list):
    grouped_files = group_files_by_number([os.path.basename(f) for f in file_list], number)
    output_filename = os.path.join(outputPath, f"{base_filename} - S{Season}E{number}.mkv")
    merge_files(grouped_files, output_filename, fonts_list, number)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, help='Output filename', required=False)
    parser.add_argument('--output', type=str, help='Output Dir', required=False)
    parser.add_argument('--input', type=str, help='Input Dir', required=False)
    parser.add_argument('--season', type=str, help='Season', required=False)
    args = parser.parse_args()

    if args.filename is not None:
        base_filename = args.filename
    if args.output is not None:
        outputPath = args.output
    if args.input is not None:
        inputPath = os.path.abspath(args.input)
    if args.season is not None:
        Season = args.season

    base_info = f'\
Startup argsument:\n\
    Output filenames: {base_filename}\n\
    Input path: {inputPath}\n\
    Output path: {outputPath}\n\
    Season: {Season}\n'

    main()
