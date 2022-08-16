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

import argparse
from reportlab import pdfgen
from reportlab.pdfgen import canvas

paperformats = {
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


def main():
    parser = argparse.ArgumentParser(
        description="""
            Create sample PDF file with specified number of pages and size
            """
    )
    parser.add_argument("pages", action="store", type=int, help="number of pages")
    parser.add_argument(
        "size",
        action="store",
        type=str.lower,
        help="standard paper format like A4, letter, ",
    )
    parser.add_argument(
        "--landscape",
        "-l",
        action="store_true",
        help="output in landscape (default: portrait)",
    )
    parser.add_argument("--bbox", "-b", action="store_true", help="draw bbox")
    args = parser.parse_args()

    if args.size not in paperformats:
        print(
            "Unknown paper format: {}. Must be one of the following "
            "standard formats: {}".format(
                args.paperformat, ", ".join(sorted(paperformats.keys()))
            )
        )

    pagesize = paperformats[args.size]
    orientation = "portrait"
    if args.landscape:
        pagesize = list(reversed(pagesize))
        orientation = "landscape"

    outfname = "{}_{}_{}.pdf".format(args.size, orientation, str(args.pages))
    cv = canvas.Canvas(outfname, pagesize)
    w, h = pagesize
    font = cv.getAvailableFonts()[0]

    for i in range(1, args.pages + 1):
        cv.setFont(font, 50)
        cv.drawCentredString(w / 2, h / 2 + 100, orientation)
        cv.drawCentredString(w / 2, h / 2 + 50, args.size)
        cv.setFont(font, 100)
        cv.drawCentredString(w / 2, h / 2 - 50, str(i))
        if args.bbox:
            cv.setLineWidth(2)
            cv.setStrokeColorRGB(255, 0, 255)
            cv.rect(5, 5, w - 10, h - 10)
        cv.showPage()
    cv.save()

    print("Created", outfname)


if __name__ == "__main__":
    main()
