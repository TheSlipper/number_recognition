import convert
import os
import argparse
import cv2
import pytesseract
import numpy as np
from random import randint
import re


def load_and_preprocess_img(input):
    img = cv2.imread(input, cv2.IMREAD_GRAYSCALE)  # Loading in grayscale for easier noise removal
    img = cv2.fastNlMeansDenoising(img, None, 13, 13, 7)
    img = cv2.threshold(img, 25, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]  # Threshold for removing background noise
    kernel = np.ones((5, 5), np.float32) / 25
    img = cv2.filter2D(img, -1, kernel)  # https://docs.opencv.org/master/d4/d13/tutorial_py_filtering.html
    return img


def recognize_in_folder(config, input_dir, console_output, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.png'):
            recognize_in_img(config, os.path.join(input_dir, filename), console_output,
                             os.path.join(output_dir, filename.replace('.png', '.txt')))


def recognize_in_img(config, input_path, console_output, output_path):
    img = load_and_preprocess_img(input_path)

    output = pytesseract.image_to_string(img, config=config)
    output.replace("-", "").replace("F", "7").replace("f", "7")
    last_num_index = -1
    i = 0
    for char in output:
        if char.isdigit():
            last_num_index = i
        i += 1

    output = output[:last_num_index]

    if console_output:
        print(output)
    if output_path is not None:
        f = open(output_path, "w")
        f.write(output)
        f.close()


def delete_working_dir(hidden_folder_path):
    try:
        for filename in os.listdir(hidden_folder_path):
            os.remove(os.path.join(hidden_folder_path, filename))
        os.rmdir(hidden_folder_path)
    except OSError:
        print('Deletion of working directory failed - do you have the permission to delete folders and files in the'
              ' current directory?')


def main():
    # Parse commandline arguments
    args = parser.parse_args()

    # Create a hidden working directory
    hidden_folder_path = os.getcwd() + '/.number_recognition/'
    try:
        os.mkdir(hidden_folder_path)
    except OSError:
        print('Creation of working directory failed: do you have the permission to the create folders in the current '
              'directory?')

    # Configuration for the tesseract
    # oem is OCR engine mode
    # and PSM is page segmentation mode (6 - Assume a single uniform block of text.)
    custom_config = r'--oem 3 --psm 6'

    # Convert image/images to png and then recognize text inside them
    if args.input_dir_path is not None:  # when working with a directory
        if not os.path.isdir(args.input_dir_path) or not os.path.isdir(args.output_dir_path):
            print("Passed input or output directory does not exist or is a file!")
        else:
            convert.convert_all_in_folder(args.input_dir_path, hidden_folder_path)
            recognize_in_folder(custom_config, hidden_folder_path, not args.mute, args.output_dir_path)
    elif args.input_file_path:  # when working with a file
        if not os.path.isfile(args.input_file_path) or not args.input_file_path.endswith('.eps'):
            print("Passed input file either does not exist or is not an eps file!")
        else:
            png_file_path = hidden_folder_path + str(randint(0, 100)) + '.png'
            convert.convert_img(args.input_file_path, png_file_path)
            recognize_in_img(custom_config, png_file_path, not args.mute, args.output_file_path)
    else:
        print("You need to specify either a target directory or a target file for recognition")

    delete_working_dir(hidden_folder_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='A small script capable of recognizing two leading numbers in eps files.')

    parser.add_argument('--input', '-i', dest='input_file_path', default='file.eps',
                        help='path to the input eps file')

    parser.add_argument('--input-dir', '-idir', dest='input_dir_path', help='path to the folder with eps files')

    parser.add_argument('--output', '-o', dest='output_file_path',
                        help='path to where the output file should be created')

    parser.add_argument('--output-dir', '-odir', dest='output_dir_path', help='path to the output folder')

    parser.add_argument('--mute', '-m', action='store_true',
                        help='if set to true will turn off all of the console output of this command')
    main()
