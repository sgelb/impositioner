#!/usr/bin/env python

import argparse
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='''
            Create sample PDF file with specified number of pages and size
            ''')
    parser.add_argument('pages', action='store', type=int,
                        help='number of pages', )
    parser.add_argument('size', action='store', type=str.upper,
                        choices=['A4', 'A5', 'A6'], help='paper size')
    args = parser.parse_args()

    size = args.size
    if size == "A4":
        pagesize = pagesizes.A4
    elif size == "A5":
        pagesize = pagesizes.A5
    elif size == "A6":
        pagesize = pagesizes.A6

    outfname = args.size + "_" + str(args.pages) + ".pdf"
    canvas = canvas.Canvas(outfname, pagesize)
    w, h = pagesize
    font = canvas.getAvailableFonts()[0]

    for i in range(1, args.pages + 1):
        canvas.setFont(font, 50)
        canvas.drawCentredString(w/2, h/2 + 50, size)
        canvas.setFont(font, 100)
        canvas.drawCentredString(w/2, h/2 - 50, str(i))
        canvas.showPage()
    canvas.save()

    print("Created", outfname)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
