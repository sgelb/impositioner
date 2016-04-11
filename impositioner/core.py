#!/usr/bin/env python

# Copyright (C) sgelb 2015

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>

import argparse
import math
import os
from pdfrw import PdfReader, PdfWriter, PageMerge
import re
import sys
import textwrap

paperformats = {
    'a0': [2384, 3371],
    'a1': [1685, 2384],
    'a2': [1190, 1684],
    'a3': [842, 1190],
    'a4': [595, 842],
    'a5': [420, 595],
    'a6': [298, 420],
    'a7': [210, 298],
    'a8': [148, 210],
    'b4': [729, 1032],
    'b5': [516, 729],
    'letter': [612, 792],
    'legal': [612, 1008],
    'ledger': [1224, 792],
    'tabloid': [792, 1224],
    'executive': [540, 720]
    }

# dots per unit
units = {
    'mm': 2.834,
    'cm': 28.34,
    'inch': 72
    }


def reverse_remainder(dividend, divisor):
    reverse_remainder = 0
    if dividend % divisor:
        reverse_remainder = divisor - dividend % divisor
    return reverse_remainder


def calculate_signature_length(page_count):
    # return page_count as signature_length if page_count too low
    if page_count <= 36:
        # make sure that page_count is a multiple of 4
        return page_count + reverse_remainder(page_count, 4)

    # calculate signature length with fewest additional blank pages. possible
    # signature lengths are 20, 24, 28, 32 and 36
    signature_length = page_count
    remainder = sys.maxsize

    for length in range(16, 36+1, 4):
        new_remainder = reverse_remainder(page_count, length)
        if new_remainder <= remainder:
            remainder = new_remainder
            signature_length = length
    return signature_length


def cut_in_signatures(inpages, signature_length):
    signatures = []
    for i in range(0, len(inpages), signature_length):
        signatures.append(inpages[i:i+signature_length])
    return signatures


def impose(pages, pages_per_sheet, binding):
    if pages_per_sheet == 1:
        return pages

    sheets = []
    half = len(pages) // 2
    rotation = 90 if math.log2(pages_per_sheet) % 2 else 270
    for i in range(0, half, 2):
        # frontside
        sheets.append(merge((pages[half+i], pages[i]), rotation, binding))
        # backside
        sheets.append(merge((pages[i+1], pages[half+i+1]),
                            (rotation+180) % 360, binding))

    return impose(sheets, pages_per_sheet // 2, binding)


def merge(pages, rotation, binding):
    result = PageMerge() + (page for page in pages)
    if binding == "left":
        result[-1].x += result[0].w
        result.rotate = rotation if is_landscape(result) else 0
    elif binding == "top":
        result[0].y += result[0].h
        result.rotate = rotation if not is_landscape(result) else 0
    elif binding == "right":
        result[0].x += result[0].w
        result.rotate = rotation if is_landscape(result) else 0
    elif binding == "bottom":
        result[-1].y += result[0].h
        result.rotate = rotation if not is_landscape(result) else 0
    else:
        print("Unknown binding", binding)
        sys.exit(1)

    return result.render()


def create_blank_copy(page):
    blank_page = PageMerge()
    blank_page.mbox = page.MediaBox
    blank_page.rotate = page.Rotate
    return blank_page.render()


def calculate_scaled_sub_page_size(pages_per_sheet, papersize):
    # return [w, h] of subpage scaled according to final output size
    if pages_per_sheet == 2:
        # columns = 2, rows = 1
        return [round(papersize[1] / 2), round(papersize[0])]

    square = math.sqrt(pages_per_sheet)
    if square.is_integer():
        # columns = rows = square, divide width and height by square
        return [round(papersize[0] / square), round(papersize[1] / square)]
    else:
        # columns is first multiple of 2 lesser than square
        columns = square - square % 2
        rows = pages_per_sheet / columns
        return [round(papersize[0] / columns), round(papersize[1] / rows)]


def add_blanks(signature, pages_per_sheet):
    remainder = len(signature) % (2 * pages_per_sheet)
    if remainder:
        blank_pages_count = ((2 * pages_per_sheet) - remainder)
        blank_page = create_blank_copy(signature[0])
        blank_pages = ([blank_page] * (blank_pages_count // 2))
        # add blanks as pairs of front- and backsides
        signature[len(signature)//2:len(signature)//2] = blank_pages
        signature.extend(blank_pages)

    return signature


def get_media_box_size(outpages):
    current_size = [int(float(value)) for value in outpages[0].media_box[-2:]]

    if outpages[0].Rotate in (90, 270):
        # at this point, rotation is not "hardcoded" into the dimensions, but
        # just noted. if the noted rotation would result in a different page
        # orientation, we switch values
        current_size = list(reversed(current_size))

    return current_size


def calculate_margins(output_size, current_size):
    scale = min(output_size[0] / current_size[0],
                output_size[1] / current_size[1])
    x_margin = round(0.5 * (output_size[0] - scale * current_size[0]))
    y_margin = round(0.5 * (output_size[1] - scale * current_size[1]))
    return scale, x_margin, y_margin


# TODO: refactor calculation of scale, x_margin and y_margin in own function
def resize(outpages, output_size):
    current_size = get_media_box_size(outpages)

    # rotate output_size if outpages would fit better
    out_ratio = output_size[0] / output_size[1]
    cur_ratio = current_size[0] / current_size[1]
    if out_ratio > 1 and cur_ratio <= 1 or out_ratio <= 1 and cur_ratio > 1:
        output_size = list(reversed(output_size))

    scale, x_margin, y_margin = calculate_margins(output_size, current_size)

    for idx, page in enumerate(outpages):
        page = PageMerge().add(page)

        # scale page
        page[0].scale(scale)
        page[0].x += x_margin
        page[0].y += y_margin

        # set new mediabox size
        page.mbox = [0, 0] + output_size

        # replace original with resized page
        outpages[idx] = page.render()

    return outpages


def is_landscape(page):
    dim = page.xobj_box[2:]
    return dim[0] > dim[1]


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='impositioner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            '''
            Impose PDF file for booklet printing
            '''),
        epilog=textwrap.dedent(
            '''
        Examples:

        Print 4 pages on an A4 sheet for creating an A6 booklet:
        $ %(prog)s -n 4 -f a4 input.pdf

        Create booklet with binding on right side and signatures of 20 pages:
        $ %(prog)s -b right -s 20 input.pdf

        Create booklet with custom output format. Center each page before
        combining:
        $ %(prog)s -f 209.5x209.5 input.pdf
        '''),
    )

    # positional argument
    parser.add_argument('PDF', action='store', help='PDF file')

    # optional arguments
    parser.add_argument('-n', dest='nup', metavar='N',
                        action='store', type=int, default="2",
                        help='Pages per sheet (default: 2)')
    parser.add_argument('-f', dest='paperformat', action='store',
                        type=str.lower, metavar='FORMAT',
                        help='Output paper sheet format. Must be standard'
                        ' paper format (A4, letter, ...) or custom'
                        ' WIDTHx_hEIGHT (default: auto)')
    parser.add_argument('-u', dest='unit', action='store',
                        default='mm', choices=['cm', 'inch', 'mm'],
                        help='Unit if using -f with custom format'
                        ' (default: mm)')
    parser.add_argument('-b', dest='binding', action='store', type=str.lower,
                        choices=['left', 'top', 'right', 'bottom'],
                        default='left',
                        help='Side of binding (default: left)')
    parser.add_argument('-c', dest='center_subpage', action='store_true',
                        help='Center each page when resizing. Has no effect if'
                        ' output format is multiple of input format (default:'
                        ' center combinated pages)')
    parser.add_argument('-s', dest='signature_length', action='store',
                        type=int,
                        help='Signature length. Set to 0 to disable signatures'
                        ' (default: auto)')
    parser.add_argument('-d', dest='divider', action='store_true',
                        default=False,
                        help='Insert blank sheets between signature stacks to'
                        ' ease separation after printing')
    parser.add_argument('-v', dest='verbose', action='store_true',
                        default=False,
                        help='Verbose output')
    return parser.parse_args()


def read_pdf(infile):
    return PdfReader(infile).pages


def validate_infile(pdf):
    infile = os.path.abspath(pdf)
    if not os.path.exists(infile):
        print("File does not exist: {}".format(infile))
        sys.exit(1)
    return infile


def validate_papersize(paperformat, unit):
    papersize = None
    if paperformat:
        # standard format
        if paperformat in paperformats:
            papersize = paperformats[paperformat]

        # custom format
        if not papersize:
            # float_xfloat
            pattern = re.compile('^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$', re.I)
            match = re.match(pattern, paperformat)
            if match:
                papersize = [round(units[unit] * float(match.group(1))),
                             round(units[unit] * float(match.group(2)))]
        # invalid input
        if not papersize:
            # FIXME: print error on stderr
            print("Unknown paper format: {}. Must be WIDTHxHEIGHT (e.g 4.3x11)"
                  " or one of the following standard formats: {}".format(
                    paperformat, ', '.join(sorted(paperformats.keys()))))
            sys.exit(1)

    return papersize


def validate_pages_per_sheet(pages_per_sheet):
    # validate nup
    if pages_per_sheet < 2:
        # FIXME: print error on stderr
        print("Pages per sheet must be a greater than 1, is {}".format(
              pages_per_sheet))
        sys.exit(1)
    if not math.log2(pages_per_sheet).is_integer():
        # FIXME: print error on stderr
        print("Pages per sheet must be a power of 2, is {}".format(
              pages_per_sheet))
        sys.exit(1)

    return pages_per_sheet


def validate_signature_length(signature_length):
    # validate signature_length argument
    if signature_length and signature_length % 4:
        print("Signature length must be multiple of 4!")
        sys.exit(1)
    return signature_length


def create_filename(infile):
    return 'booklet.' + os.path.basename(infile)


def save_pdf(infile, outpages):
    trailer = PdfReader(infile)
    outfn = create_filename(infile)
    writer = PdfWriter()
    writer.addpages(outpages)
    writer.trailer.Info = trailer.Info
    writer.trailer.Info.Producer = "https://github.com/sgelb/impositioner"
    writer.write(outfn)


def main():
    args = parse_arguments()

    # validate cli arguments
    infile = validate_infile(args.PDF)
    signature_length = validate_signature_length(args.signature_length)
    papersize = validate_papersize(args.paperformat, args.unit)
    pages_per_sheet = validate_pages_per_sheet(args.nup)

    # read pdf file
    inpages = PdfReader(infile).pages

    # calculate some variables
    page_count = len(inpages)

    # signatures are disabled
    if not signature_length:
        signature_length = page_count + reverse_remainder(page_count, 4)

    # signature_length is neither manually set nor disabled, calculate length
    if not signature_length:
        signature_length = calculate_signature_length(page_count)

    signature_count = math.ceil(page_count / signature_length)

    # add blank pages
    blank_pages_count = signature_length * signature_count - page_count
    if blank_pages_count:
        inpages.extend([create_blank_copy(inpages[0])] * blank_pages_count)

    # calculate output size of single page for centering content
    if papersize and args.center_subpage:
        output_size = calculate_scaled_sub_page_size(
            pages_per_sheet, papersize)

    # start impositioning
    outpages = []
    # split pages in signatures
    for signature in cut_in_signatures(inpages, signature_length):
        # reverse second half of signature to simplify imposition
        signature[len(signature)//2:] = list(
                reversed(signature[len(signature)//2:]))

        # add blank pages
        signature = add_blanks(signature, pages_per_sheet)

        # resize pages before merging
        if papersize and args.center_subpage:
            signature = resize(signature, output_size)

        # impose each signature
        outpages.extend(impose(signature, pages_per_sheet, args.binding))

        # add divider pages
        if args.divider:
            outpages.append(create_blank_copy(outpages[0]))
            outpages.append(create_blank_copy(outpages[0]))

    # remove divider pages at end
    if args.divider:
        del outpages[-2:]

    # resize result
    if papersize:
        outpages = resize(outpages, papersize)

    # print infos
    if args.verbose:
        for line in textwrap.wrap(
            "Standard paper formats: {}".format(
                ', '.join(sorted(paperformats.keys()))), 80):
            print(line)
        print("Total input page:  {:>3}".format(page_count))
        print("Total output page: {:>3}".format(len(outpages)))

        input_size = inpages[0].media_box[2:]
        output_size = outpages[0].media_box[2:]
        print("Input size:        {}x{}".format(input_size[0], input_size[1]))
        print("Output size:       {}x{}".format(int(output_size[0]),
                                                int(output_size[1])))

        print("Signature length:  {:>3}".format(signature_length))
        print("Signature count:   {:>3}".format(signature_count))
        divider_count = 2*signature_count - 2 if args.divider else 0
        print("Divider pages:     {:>3}".format(divider_count))

    # save imposed pdf
    save_pdf(infile, outpages)
    print("Imposed PDF file saved to {}".format(create_filename(infile)))


if __name__ == '__main__':
    main()
