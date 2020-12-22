import argparse
import json
import logging
from struct import *


def get_section_header(file, offset):
    file.seek(offset, 0)
    section_header_data = file.read(8)
    section_header = unpack('<II', section_header_data)
    byte_size = section_header[0]
    element_count = section_header[1]
    logging.debug(f'Section size: {byte_size} bytes | element_count {element_count}')
    return element_count


# Strings are stored as a length descriptor byte then a null terminated string
def get_string(file) -> str:
    string_length = int.from_bytes(file.read(1), byteorder='little', signed=False)
    string_bytes = []
    for index in range(string_length):
        character = chr(int.from_bytes(file.read(1), byteorder='little', signed=False))
        string_bytes.append(character)
    # Remove the null terminator when returning the string
    return ''.join(string_bytes[:-1])


def decompile(scenario_file, out_path) -> None:
    logging.info(f'Parsing file header.')
    with open(scenario_file, "rb") as file:
        data = file.read(80)
        header = unpack('<IIIIIIIIIIIIIIIIIIII', data)

        logging.info(f'Magic: {hex(header[0])}')
        logging.info(f'Size: {header[1]} bytes')
        logging.debug(f'script_offset: {hex(header[8])}')
        logging.debug(f'offset_36: {hex(header[9])}')
        logging.debug(f'offset_40: {hex(header[10])}')
        logging.debug(f'offset_44: {hex(header[11])}')
        logging.debug(f'offset_52: {hex(header[13])}')
        logging.debug(f'offset_56: {hex(header[14])}')
        logging.debug(f'offset_60: {hex(header[15])}')

        script_offset = header[8]

        # Section_36 - Masks
        section_36_list = section_36(file, header)
        logging.debug(section_36_list)

        # Section_40 - Backgrounds
        section_40_list = section_40(file, header)
        logging.debug(section_40_list)

        # Section_44 - Bustup
        section_44_list = section_44(file, header)
        logging.debug(section_44_list)

        # Section_52 - Sound Effects
        section_52_list = section_52(file, header)
        logging.debug(section_52_list)

        # Section_56 - Movies
        section_56_list = section_56(file, header)
        logging.debug(section_56_list)

        # Section_60 - Voice
        section_60_list = section_60(file, header)
        logging.debug(section_60_list)

        # Done reading header, dump it to a file
        out_dict = {
            'Section_36': section_36_list,
            'Section_40': section_40_list,
            'Section_44': section_44_list,
            'Section_52': section_52_list,
            'Section_56': section_56_list,
            'Section_60': section_60_list
        }
        with open(out_path + '/head_data.json', "w") as out_file:
            json.dump(out_dict, out_file)
        logging.info(f'Header JSON written.')

        # Dump commands section
        with open(out_path + '/code_dump.bin', "wb") as out_file:
            file.seek(script_offset, 0)
            while byte := file.read(1):
                out_file.write(byte)
        logging.info(f'Code section dump written.')

        # Parse Script
        script_section(file, header, out_path)


# Masks
def section_36(file, header):
    element_count = get_section_header(file, header[9])
    section_36_list = []
    for index in range(element_count):
        section_36_list.append(get_string(file))
    return section_36_list


# Backgrounds
def section_40(file, header):
    element_count = get_section_header(file, header[10])
    section_40_list = []
    for index in range(element_count):
        item1 = get_string(file)
        item2 = int.from_bytes(file.read(2), byteorder='little', signed=False)
        section_40_list.append({'item1': item1, 'item2': item2})
    return section_40_list


# Bustup
def section_44(file, header):
    element_count = get_section_header(file, header[11])
    section_44_list = []
    for index in range(element_count):
        item1 = get_string(file)
        item2 = get_string(file)
        item3 = int.from_bytes(file.read(2), byteorder='little', signed=False)
        section_44_list.append({'item1': item1, 'item2': item2, 'item3': item3})
    return section_44_list


# Sound Effects
def section_52(file, header):
    element_count = get_section_header(file, header[13])
    section_52_list = []
    for index in range(element_count):
        section_52_list.append(get_string(file))
    return section_52_list


# Movies
def section_56(file, header):
    element_count = get_section_header(file, header[14])
    section_56_list = []
    for index in range(element_count):
        item1 = get_string(file)
        item2 = int.from_bytes(file.read(4), byteorder='little', signed=False)
        section_56_list.append({'item1': item1, 'item2': item2})
    return section_56_list


# Voice
def section_60(file, header):
    element_count = get_section_header(file, header[15])
    section_60_list = []
    for index in range(element_count):
        item1 = get_string(file)
        file.read(1)
        item2 = int.from_bytes(file.read(1), byteorder='little', signed=False)
        section_60_list.append({'item1': item1, 'item2': item2})
    return section_60_list


def script_section(file, header, out_path):
    size = header[1]
    commands_offset = header[8]
    code_size = size - commands_offset
    element_count = get_section_header(file, commands_offset)


if __name__ in ('__main__', '__builtin__', 'builtins'):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='Parse the Scenario file for Konosuba Labyrinth+ on Switch')
    parser.add_argument('-s', '--scenario', required=False, default='main.snr', help='Path to Scenario file to parse')
    parser.add_argument('-o', '--out', required=False, default='.', help='Path to folder for output')
    parser.add_argument('-c', '--command', required=False, default='decompile', action='store')
    args = parser.parse_args()

    if args.command == 'decompile':
        decompile(args.scenario, args.out)
