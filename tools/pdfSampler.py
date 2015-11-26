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
    parser.add_argument('--landscape', '-l', action='store_true',
                        help='output in landscape (default: portrait)')
    args = parser.parse_args()

    size = args.size
    if size == "A4":
        pagesize = pagesizes.A4
    elif size == "A5":
        pagesize = pagesizes.A5
    elif size == "A6":
        pagesize = pagesizes.A6

    orientation = "P"
    if args.landscape:
        pagesize = pagesizes.landscape(pagesize)
        orientation = "L"

    outfname = "{}_{}_{}.pdf".format(args.size, str(args.pages), orientation)
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
