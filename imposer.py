#!/usr/bin/env python

# First modified: 2015-11-15, 19:10

import argparse
import os
import sys
import math
from pdfrw import PdfReader, PdfWriter, PageMerge


def getPageSize(page):
    return PageMerge().add(page)[0]['/BBox'][2:]


def calculateSignatureLength(pageCount):
    # return pageCount as signatureLength if pageCount too low
    if pageCount <= 36:
        # make sure that pageCount is even
        if pageCount % 2:
            return pageCount + 1
        else:
            return pageCount

    # calculate signaturelength with as less additional blank pages as possible
    signatureLength = pageCount
    remainder = sys.maxsize

    # possible signature lengths: 20, 24, 28, 32, 36
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


def merge(*pages):
    result = PageMerge() + (x for x in pages if x is not None)
    result[-1].x += result[0].w
    result.rotate = 90
    return result.render()


def impose(pages):
    opages = []
    while len(pages) > 2:
        opages.append(merge(pages.pop(), pages.pop(0)))
        opages.append(merge(pages.pop(0), pages.pop()))
    opages += pages
    return opages


if __name__ == '__main__':
    # TODO:
    # options:
    # - input format to output format + scale or NxN + scale
    # - number of pages per signature
    # - illustrated help for folding/cutting
    # - add cut line?
    # - creep/shingling/push out?

    parser = argparse.ArgumentParser(
            description='''
            Impose PDF file.

            (TODO: rephrase description)

            Default is to imposition without scaling => -n defines output
            paper size. Can be overwritten by -p. Automatic calculation of
            signatures if more than 36 pages. Manual setting of signatures with
            -s.
            ''')
    parser.add_argument('PDF', action='store', help='PDF file')
    parser.add_argument('-n', dest='nup', action='store', default=2, type=int,
                        help='pages per sheet (default: 2)')
    parser.add_argument('-p', dest='papersize', action='store',
                        choices=['A4', 'A5', 'A6'], help='output paper size '
                        '(default: auto)')
    parser.add_argument('-s', dest='signatureLength', action='store', type=int,
                        help='Set signature length (default: auto)')
    args = parser.parse_args()

    # validate arguments
    infile = os.path.abspath(args.PDF)
    if not os.path.exists(infile):
        print("File does not exist:", infile)
        sys.exit(1)

    signatureLength = args.signatureLength
    if signatureLength and signatureLength % 4:
        print("Signature length must be multiple of 4!")
        sys.exit(1)

    # read pdf file
    inpages = PdfReader(infile).pages

    # calculate some variables
    pageSize = getPageSize(inpages[0])
    pageCount = len(inpages)
    if not signatureLength:
        signatureLength = calculateSignatureLength(pageCount)
    signatureCount = math.ceil(pageCount / signatureLength)
    additionalBlankPagesCount = signatureLength * signatureCount - pageCount
    totalPageCount = pageCount + additionalBlankPagesCount

    # add blank pages
    for i in range(additionalBlankPagesCount):
        inpages.append(None)

    outpages = []
    # split pages in signatures
    for signature in getSignaturePages(inpages, signatureLength):
        # simple 2x1 imposition
        outpages.extend(impose(signature))

    # save imposed pdf
    outfn = 'booklet.' + os.path.basename(infile)
    print("Save imposed pdf to", outfn)
    PdfWriter().addpages(outpages).write(outfn)

    # print("Page size (pts):", pageSize)
    # print("Page count:", pageCount)
    # print("Signature length:", signatureLength)
    # print("Needed blanks:", additionalBlankPagesCount)
    # print("Total pages:", pageCount + additionalBlankPagesCount)


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
