#!/usr/bin/env python

# Copyright (C) sgelb 2019

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

import math
import os
from pdfrw import PdfReader, PdfWriter, PageMerge
import re
import sys

from typing import Dict, List, Iterator, Optional, Any, Tuple

paperformats: Dict[str, List[int]] = {
    "a0": [2384, 3371],
    "a1": [1685, 2384],
    "a2": [1190, 1684],
    "a3": [842, 1190],
    "a4": [595, 842],
    "a5": [420, 595],
    "a6": [298, 420],
    "a7": [210, 298],
    "a8": [148, 210],
    "b4": [729, 1032],
    "b5": [516, 729],
    "letter": [612, 792],
    "legal": [612, 1008],
    "ledger": [1224, 792],
    "tabloid": [792, 1224],
    "executive": [540, 720],
}

# dots per unit
units: Dict[str, float] = {"mm": 2.834, "cm": 28.34, "inch": 72}


def reverse_remainder(dividend: int, divisor: int) -> int:
    reverse_remainder = 0
    if dividend % divisor:
        reverse_remainder = divisor - dividend % divisor
    return reverse_remainder


def calculate_signature_length(page_count: int) -> int:
    # return page_count as signature_length if page_count too low
    if page_count <= 36:
        # make sure that page_count is a multiple of 4
        return page_count + reverse_remainder(page_count, 4)

    # calculate signature length with fewest additional blank pages. if two
    # lengths add the same amount of blank pages, choose the larger one.
    # possible signature lengths are 20, 24, 28, 32 and 36 pages.
    signature_length = page_count
    remainder = sys.maxsize

    for length in range(20, 36 + 1, 4):
        new_remainder = reverse_remainder(page_count, length)
        if new_remainder <= remainder:  # change to < to choose smaller length
            remainder = new_remainder
            signature_length = length
    return signature_length


def cut_in_signatures(inpages: List, signature_length: int) -> Iterator[List]:
    for i in range(0, len(inpages), signature_length):
        yield inpages[i : i + signature_length]


def impose(pages: List, pages_per_sheet: int, binding: str) -> List:
    if pages_per_sheet == 1:
        return pages

    sheets = []
    half = len(pages) // 2
    rotation = 90 if math.log2(pages_per_sheet) % 2 else 270
    for i in range(0, half, 2):
        # frontside
        sheets.append(merge((pages[half + i], pages[i]), rotation, binding))
        # backside
        sheets.append(
            merge((pages[i + 1], pages[half + i + 1]), (rotation + 180) % 360, binding)
        )

    return impose(sheets, pages_per_sheet // 2, binding)


def merge(pages, rotation, binding) -> Any:
    page = PageMerge() + (p for p in pages)
    page = set_binding(page, binding, rotation)
    return page.render()


def set_binding(page, binding, rotation):
    if binding == "left":
        page[1].x += page[0].w
        page.rotate = rotation if is_landscape(page) else 0
    elif binding == "top":
        page[0].y += page[0].h
        page.rotate = rotation if not is_landscape(page) else 0
    elif binding == "right":
        page[0].x += page[0].w
        page.rotate = rotation if is_landscape(page) else 0
    elif binding == "bottom":
        page[1].y += page[0].h
        page.rotate = rotation if not is_landscape(page) else 0
    else:
        print("Unknown binding:", binding)
        sys.exit(1)
    return page


def create_blank_copy(page) -> Any:
    blank_page = PageMerge()
    blank_page.mbox = page.MediaBox
    blank_page.rotate = page.Rotate
    return blank_page.render()


def calculate_scaled_sub_page_size(
    pages_per_sheet: int, papersize: Optional[Dict]
) -> List[int]:
    # return [w, h] of subpage scaled according to final output size
    if pages_per_sheet == 2:
        # columns = 2, rows = 1
        return [int(round(papersize[1] / 2)), int(round(papersize[0]))]

    square = math.sqrt(pages_per_sheet)
    if square.is_integer():
        # columns = rows = square, divide width and height by square
        return [int(round(papersize[0] / square)), int(round(papersize[1] / square))]
    else:
        # columns is first multiple of 2 lesser than square
        columns = square - square % 2
        rows = pages_per_sheet / columns
        return [int(round(papersize[0] / columns)), int(round(papersize[1] / rows))]


def add_blanks(signature: List, pages_per_sheet: int) -> List:
    remainder = len(signature) % (2 * pages_per_sheet)
    s = list(signature)
    if remainder:
        blank_pages_count = (2 * pages_per_sheet) - remainder
        blank_page = create_blank_copy(signature[0])
        blank_pages = [blank_page] * (blank_pages_count // 2)
        # add blanks as pairs of front- and backsides
        s[len(signature) // 2 : len(signature) // 2] = blank_pages
        s.extend(blank_pages)

    return s


def get_media_box_size(outpages) -> List[int]:
    current_size = [int(float(value)) for value in outpages[0].MediaBox[-2:]]

    if outpages[0].Rotate in (90, 270):
        # at this point, rotation is not "hardcoded" into the dimensions, but
        # just noted. if the noted rotation would result in a different page
        # orientation, we switch values
        current_size = list(reversed(current_size))

    return current_size


def calculate_margins(output_size, current_size) -> Tuple[Any, float, float]:
    scale = min(output_size[0] / current_size[0], output_size[1] / current_size[1])
    x_margin = round(0.5 * (output_size[0] - scale * current_size[0]))
    y_margin = round(0.5 * (output_size[1] - scale * current_size[1]))
    return scale, x_margin, y_margin


def resize(outpages: List, output_size: List[int]) -> List:
    current_size = get_media_box_size(outpages)
    o = list(outpages)

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
        o[idx] = page.render()

    return o


def is_landscape(page) -> Any:
    dim = page.xobj_box[2:]
    return dim[0] > dim[1]


def validate_infile(pdf: str) -> str:
    infile = os.path.abspath(pdf)
    if not os.path.exists(infile):
        print("File does not exist: {}".format(infile))
        sys.exit(1)
    return infile


def validate_papersize(paperformat: str, unit: str) -> Optional[List[int]]:
    papersize: List[int] = None
    if paperformat:
        # standard format
        if paperformat in paperformats:
            papersize = paperformats[paperformat]

        # custom format
        else:
            # floatxfloat
            pattern = re.compile(r"^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$", re.I)
            match = re.match(pattern, paperformat)
            if match:
                papersize = [
                    int(round(units[unit] * float(match.group(1)))),
                    int(round(units[unit] * float(match.group(2)))),
                ]
            else:
                # invalid input
                print(
                    "Unknown paper format: {}. Must be WIDTHxHEIGHT (e.g 4.3x11)"
                    " or one of the following standard formats: {}".format(
                        paperformat, ", ".join(sorted(paperformats.keys()))
                    )
                )
                sys.exit(1)

    return papersize


def validate_pages_per_sheet(pages_per_sheet: int) -> int:
    # validate nup
    if pages_per_sheet < 2:
        print("Pages per sheet must be a greater than 1, is {}".format(pages_per_sheet))
        sys.exit(1)
    if not math.log2(pages_per_sheet).is_integer():
        print("Pages per sheet must be a power of 2, is {}".format(pages_per_sheet))
        sys.exit(1)

    return pages_per_sheet


def validate_signature_length(signature_length: int) -> int:
    # validate signature_length argument
    if signature_length > 0 and signature_length % 4:
        print("Signature length must be multiple of 4, is {}".format(signature_length))
        sys.exit(1)
    return signature_length


def impose_and_merge(
    inpages: List,
    signature_length: int,
    pages_per_sheet: int,
    output_size: List[int],
    binding: str,
) -> List:
    sheets = []
    for signature in cut_in_signatures(inpages, signature_length):
        # reverse second half of signature to simplify imposition
        signature[len(signature) // 2 :] = list(
            reversed(signature[len(signature) // 2 :])
        )

        # add blank pages
        signature = add_blanks(signature, pages_per_sheet)

        # resize/center pages before merging
        if output_size:
            signature = resize(signature, output_size)

        # impose each signature
        signature = impose(signature, pages_per_sheet, binding)

        # extend sheets
        sheets.extend(signature)

    return sheets


def add_divider(sheets: List, signature_length: int) -> List:
    s = list(sheets)
    divider = create_blank_copy(sheets[0])
    for i in range(signature_length // 2, len(sheets), signature_length // 2):
        s.insert(i, divider)
        s.insert(i, divider)
    return s


def create_filename(infile) -> str:
    return "booklet." + os.path.basename(infile)


def save_pdf(infile, outpages) -> None:
    trailer = PdfReader(infile)
    outfn = create_filename(infile)
    writer = PdfWriter()
    writer.addpages(outpages)
    writer.trailer.Info = trailer.Info
    writer.trailer.Info.Producer = "https://github.com/sgelb/impositioner"
    writer.write(outfn)
