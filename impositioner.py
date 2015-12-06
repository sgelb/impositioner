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


def calculateSignatureLength(pageCount):
    # return pageCount as signatureLength if pageCount too low
    if pageCount <= 36:
        # make sure that pageCount is a multiple of 4
        if pageCount % 4:
            pageCount += 4 - pageCount % 4
        return pageCount

    # calculate signature length with fewest additional blank pages. possible
    # signature lengths are 20, 24, 28, 32 and 36
    signatureLength = pageCount
    remainder = sys.maxsize

    for length in range(16, 36+1, 4):
        if length - pageCount % length <= remainder:
            remainder = length - pageCount % length
            signatureLength = length
    return signatureLength


def getSignaturePages(inpages, signatureLength):
    signatures = []
    for i in range(0, len(inpages), signatureLength):
        signatures.append(inpages[i:i+signatureLength])
    return signatures


def impose(pages, pagesPerSheet, binding):
    if pagesPerSheet == 1:
        return pages

    npages = []
    half = len(pages) // 2
    rotation = 90 if math.log2(pagesPerSheet) % 2 else 270
    for i in range(0, half, 2):
        # frontside
        npages.append(merge((pages[half+i], pages[i]), rotation, binding))
        # backside
        npages.append(merge((pages[i+1], pages[half+i+1]),
                            (rotation+180) % 360, binding))

    return impose(npages, pagesPerSheet // 2, binding)


def merge(pages, rotation, binding):
    result = PageMerge() + (page for page in pages)
    if binding == "left":
        result[-1].x += result[0].w
        result.rotate = rotation if isLandscape(result) else 0
    elif binding == "top":
        result[0].y += result[0].h
        result.rotate = rotation if not isLandscape(result) else 0
    elif binding == "right":
        result[0].x += result[0].w
        result.rotate = rotation if isLandscape(result) else 0
    elif binding == "bottom":
        result[-1].y += result[0].h
        result.rotate = rotation if not isLandscape(result) else 0
    else:
        print("Unknown binding", binding)
        sys.exit(1)

    return result.render()


def calculateScaledSubPageSize(pagesPerSheet, papersize):
    # return [w, h] of subpage scaled according to final output size
    if pagesPerSheet == 2:
        # columns = 2, rows = 1
        return [round(papersize[1] / 2), round(papersize[0])]

    square = math.sqrt(pagesPerSheet)
    if square.is_integer():
        # columns = rows = square, divide width and height by square
        return [round(papersize[0] / square), round(papersize[1] / square)]
    else:
        # columns is first multiple of 2 lesser than square
        columns = square - square % 2
        rows = pagesPerSheet / columns
        return [round(papersize[0] / columns), round(papersize[1] / rows)]


def resize(outpages, outputSize):
    currentSize = [int(float(value)) for value in outpages[0].MediaBox[-2:]]

    if outpages[0].Rotate in (90, 270):
        # at this point, rotation is not "hardcoded" into the dimensions, but
        # just noted. if the noted rotation would result in a different page
        # orientation, we switch values
        currentSize = list(reversed(currentSize))

    # rotate outputSize if outpages would fit better
    outRatio = outputSize[0] / outputSize[1]
    curRatio = currentSize[0] / currentSize[1]
    if (outRatio > 1 and curRatio <= 1) or (outRatio <= 1 and curRatio > 1):
        outputSize = list(reversed(outputSize))

    scale = min(outputSize[0] / currentSize[0], outputSize[1] / currentSize[1])
    xMargin = round(0.5 * (outputSize[0] - scale * currentSize[0]))
    yMargin = round(0.5 * (outputSize[1] - scale * currentSize[1]))

    for idx, page in enumerate(outpages):
        page = PageMerge().add(page)

        # scale page
        page[0].scale(scale)
        page[0].x += xMargin
        page[0].y += yMargin

        # set new mediabox size
        page.mbox = [0, 0] + outputSize

        # replace original with resized page
        outpages[idx] = page.render()

    return outpages


def isLandscape(page):
    dim = page.xobj_box[2:]
    return dim[0] > dim[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            '''
            Impose PDF file for booklet printing
            '''),
        epilog=textwrap.dedent(
            '''
        Examples:

        Print 4 pages on A4, creating an A6 booklet:
        $ {0} -n 4 -f a4 input.pdf

        Create booklet with binding on right side and signatures of 20 pages:
        $ {0} -b right -s 20 input.pdf

        Create booklet with custom output format. Center each page before
        combining:
        $ {0} -f 209.5x209.5 input.pdf
        '''.format(sys.argv[0]))
    )

    # positional argument
    parser.add_argument('PDF', action='store', help='PDF file')

    # optional arguments
    parser.add_argument('-n', dest='nup', metavar='N',
                        action='store', type=int, default="2",
                        help='Pages per sheet (default: 2)')
    parser.add_argument('-f', dest='paperformat', action='store',
                        type=str.lower, metavar='FORMAT',
                        help='Output paper format. Must be standard'
                        ' paper format (A4, letter, ...) or custom'
                        ' WIDTHxHEIGHT (default: auto)')
    parser.add_argument('-u', dest='unit', action='store',
                        default='mm', choices=['cm', 'inch', 'mm'],
                        help='Unit if using -f with custom format'
                        ' (default: mm)')
    parser.add_argument('-b', dest='binding', action='store', type=str.lower,
                        choices=['left', 'top', 'right', 'bottom'],
                        default='left',
                        help='Side of binding (default: left)')
    parser.add_argument('-c', dest='centerSubpage', action='store_true',
                        help='Center each page when resizing. Has no effect if'
                        ' output format is multiple of input format (default:'
                        ' center combinated pages)')
    parser.add_argument('-s', dest='signatureLength', action='store', type=int,
                        help='Signature length (default: auto)')
    args = parser.parse_args()

    # validate infile argument
    infile = os.path.abspath(args.PDF)
    if not os.path.exists(infile):
        print("File does not exist: {}".format(infile))
        sys.exit(1)

    # validate paperformat
    papersize = None
    if args.paperformat:
        # standard format
        if args.paperformat in paperformats:
            papersize = paperformats[args.paperformat]

        # custom format
        if not papersize:
            # floatXfloat
            pattern = re.compile('^([0-9]*\.?[0-9]+)x([0-9]*\.?[0-9]+)$', re.I)
            match = re.match(pattern, args.paperformat)
            if match:
                papersize = [round(units[args.unit] * float(match.group(1))),
                             round(units[args.unit] * float(match.group(2)))]
        # invalid input
        if not papersize:
            print("Unknown paper format: {}. Must be WIDTHxHEIGHT (e.g 4.3x11)"
                  " or one of the following standard formats: {}".format(
                    args.paperformat, ', '.join(sorted(paperformats.keys()))))
            sys.exit(1)

    # validate nup
    pagesPerSheet = args.nup
    if pagesPerSheet < 2:
        print("Pages per sheet must be a greater than 1, is {}".format(
              pagesPerSheet))
        sys.exit(1)
    if not math.log2(pagesPerSheet).is_integer():
        print("Pages per sheet must be a power of 2, is {}".format(
              pagesPerSheet))
        sys.exit(1)

    # validate signatureLength argument
    signatureLength = args.signatureLength
    if signatureLength and signatureLength % 4:
        print("Signature length must be multiple of 4!")
        sys.exit(1)

    # read pdf file
    inpages = PdfReader(infile).pages

    # calculate some variables
    pageCount = len(inpages)
    if not signatureLength:
        signatureLength = calculateSignatureLength(pageCount)
    signatureCount = math.ceil(pageCount / signatureLength)

    # add blank pages
    blankPagesCount = signatureLength * signatureCount - pageCount
    if blankPagesCount:
        blank = PageMerge()
        blank.mbox = inpages[0].MediaBox
        inpages.extend([blank.render()] * blankPagesCount)

    # calculate output size of single page for centering content
    if papersize and args.centerSubpage:
        outputSize = calculateScaledSubPageSize(pagesPerSheet, papersize)

    # impose
    outpages = []
    # split pages in signatures
    for signature in getSignaturePages(inpages, signatureLength):
        # reverse second half of signature to simplify imposition
        signature[len(signature)//2:] = list(
                reversed(signature[len(signature)//2:]))

        # resize pages before merging
        if papersize and args.centerSubpage:
            signature = resize(signature, outputSize)

        # impose each signature
        outpages.extend(impose(signature, pagesPerSheet, args.binding))

    # resize result
    if papersize:
        outpages = resize(outpages, papersize)

    # save imposed pdf
    outfn = 'booklet.' + os.path.basename(infile)
    print("Imposed PDF file saved to {}".format(outfn))
    PdfWriter().addpages(outpages).write(outfn)
