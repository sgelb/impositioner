#!/usr/bin/env python

# First modified: 2015-11-15, 19:10

import os
import sys
import math
from pdfrw import PdfReader, PdfWriter, PageMerge


def getPageSize(page):
    return PageMerge().add(page)[0]['/BBox'][2:]


def calculateSignatureLength(pageCount):
    if pageCount <= 36:
        if pageCount % 2:
            return pageCount + 1
        else:
            return pageCount

    length = pageCount
    remainder = sys.maxsize

    # possible signature lengths: 20, 24, 28, 32, 36
    for l in range(16, 36+1, 4):
        if l - pageCount % l <= remainder:
            remainder = l - pageCount % l
            length = l
    return length


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
    # - creep/shingling/push out?

    if len(sys.argv) != 2:
        print("Wrong number of arguments!")
        sys.exit()

    infile = sys.argv[1]
    inpages = PdfReader(infile).pages

    # calculate some variables
    pageSize = getPageSize(inpages[0])
    pageCount = len(inpages)
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
