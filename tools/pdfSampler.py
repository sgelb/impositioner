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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='''
            Create sample PDF file with specified number of pages and size
            ''')
    parser.add_argument('pages', action='store', type=int,
                        help='number of pages', )
    parser.add_argument('size', action='store', type=str.lower,
                        help='standard paper format like A4, letter, ')
    parser.add_argument('--landscape', '-l', action='store_true',
                        help='output in landscape (default: portrait)')
    parser.add_argument('--bbox', '-b', action='store_true',
                        help='draw bbox')
    args = parser.parse_args()

    if args.size not in paperformats:
        print("Unknown paper format: {}. Must be one of the following "
              "standard formats: {}".format(
                    args.paperformat, ', '.join(sorted(paperformats.keys()))))

    pagesize = paperformats[args.size]
    orientation = "P"
    if args.landscape:
        pagesize = list(reversed(pagesize))
        orientation = "L"

    outfname = "{}_{}_{}.pdf".format(args.size, str(args.pages), orientation)
    canvas = canvas.Canvas(outfname, pagesize)
    w, h = pagesize
    font = canvas.getAvailableFonts()[0]

    for i in range(1, args.pages + 1):
        canvas.setFont(font, 50)
        canvas.drawCentredString(w/2, h/2 + 50, args.size)
        canvas.setFont(font, 100)
        canvas.drawCentredString(w/2, h/2 - 50, str(i))
        if args.bbox:
            canvas.setLineWidth(5)
            canvas.setStrokeColorRGB(255, 0, 255)
            canvas.rect(5, 5, w - 10, h - 10)
        canvas.showPage()
    canvas.save()

    print("Created", outfname)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
