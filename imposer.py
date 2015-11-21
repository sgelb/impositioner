#!/usr/bin/env python

import argparse
import os
import sys
import math
from pdfrw import PdfReader, PdfWriter, PageMerge


paperformats = {
    'a0': (2384, 3371),
    'a1': (1685, 2384),
    'a2': (1190, 1684),
    'a3': (842, 1190),
    'a4': (595, 842),
    'a5': (420, 595),
    'a6': (298, 420),
    'a7': (210, 298),
    'a8': (148, 210),
    'b4': (729, 1032),
    'b5': (516, 729),
    'letter': (612, 792),
    'legal': (612, 1008),
    'ledger': (1224, 792),
    'tabloid': (792, 1224),
    'executive': (540, 720)
    }


def getPageSize(page):
    return PageMerge().add(page)[0]['/BBox']


def calculateSignatureLength(pageCount):
    # return pageCount as signatureLength if pageCount too low
    if pageCount <= 36:
        # make sure that pageCount is a multiple of 4
        if pageCount % 4:
            pageCount += 4 - pageCount % 4
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


def split(pages, pagesPerSheet):
    '''split pages in pagesPerSheet parts of equal lenght'''
    length = len(pages)
    npages = []
    for i in range(pagesPerSheet):
        start = i * length // pagesPerSheet
        end = (i + 1) * length // pagesPerSheet
        npages.append(pages[start:end])
    return npages


def impose(pages, pagesPerSheet):
    if pagesPerSheet == 1:
        return pages

    npages = []
    half = len(pages) // 2
    rotation = 90 if math.log2(pagesPerSheet) % 2 else 270
    for i in range(0, half, 2):
        # frontside
        npages.append(merge((pages[half+i], pages[i]), rotation))
        # backside
        npages.append(merge((pages[i+1], pages[half+i+1]),
                            (rotation+180) % 360))

    return impose(npages, pagesPerSheet // 2)


def merge(pages, rotation):
    # merge pages, using two rows
    result = PageMerge() + (page for page in pages)
    result[-1].x += result[0].w
    result = result.render()
    result.Rotate = rotation
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='''
            Impose PDF file.
            ''')

    parser.add_argument('PDF', action='store', help='PDF file')
    parser.add_argument('-n', dest='nup', action='store', type=int,
                        default="2", help='pages per sheet (default: 2)')
    parser.add_argument('-p', dest='papersize', action='store',
                        help='output paper size (default: auto)')
    parser.add_argument('-s', dest='stretch', action='store_true',
                        help='stretch pages when resizing. may change aspect '
                        ' ratio (default: false)')
    parser.add_argument('-l', dest='signatureLength', action='store', type=int,
                        help='Set signature length (default: auto)')
    args = parser.parse_args()

    # validate infile argument
    infile = os.path.abspath(args.PDF)
    if not os.path.exists(infile):
        print("File does not exist: {}".format(infile))
        sys.exit(1)

    # validate papersize
    papersize = args.papersize
    if papersize and papersize.lower() not in paperformats:
        print("Unknown papersize: {}. Valid sizes: {}".format(
            papersize, ', '.join(sorted(paperformats.keys()))))
        sys.exit(1)

    # validate nup
    pagesPerSheet = args.nup
    if pagesPerSheet:
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
    # pageSize = getPageSize(inpages[0])
    # totalPageCount = pageCount + additionalBlankPagesCount

    # add blank pages
    blankPagesCount = signatureLength * signatureCount - pageCount
    if blankPagesCount:
        blank = PageMerge()
        blank.mbox = inpages[0].MediaBox
        inpages.extend([blank.render()] * blankPagesCount)

    # impose
    outpages = []
    # split pages in signatures
    for signature in getSignaturePages(inpages, signatureLength):
        # reverse second half of signature to simplify imposition
        signature[len(signature)//2:] = list(
                reversed(signature[len(signature)//2:]))

        # impose each signature
        outpages.extend(impose(signature, pagesPerSheet))

    # resize
    if papersize:
        print("Resize")
        if args.stretch:
            # TODO: implement resizing stretching pages
            print("dont keep ratio")
        else:
            # TODO: implement resizing keeping aspect pages
            print("keep ratio")
        # o = PageMerge().add(outpages[0])
        # o[0].scale(0.5)
        # outpages[0] = o.render()
        # outpages = resize(outpages, args.papersize)

    # save imposed pdf
    outfn = 'booklet.' + os.path.basename(infile)
    print("Save imposed pdf to", outfn)
    PdfWriter().addpages(outpages).write(outfn)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
