#!/usr/bin/env python
"""
Main entry point for command-line program, invoke as `impositioner'
"""

from sys import exit
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
import textwrap
from pdfrw import PdfReader
import math

from . import core
from . import __version__

from typing import Dict, List


def parse_arguments() -> Namespace:
    parser = ArgumentParser(
        prog="impositioner",
        formatter_class=RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Impose PDF file for booklet printing
            """
        ),
        epilog=textwrap.dedent(
            """
        Examples:

        Print 4 pages on an A4 sheet for creating an A6 booklet:
        $ %(prog)s -n 4 -f a4 input.pdf

        Create booklet with binding on right side and signatures of 20 pages:
        $ %(prog)s -b right -s 20 input.pdf

        Create booklet with custom output format. Center each page before
        combining:
        $ %(prog)s -f 209.5x209.5 -c input.pdf
        """
        ),
    )

    # positional argument
    parser.add_argument("PDF", action="store", help="PDF file")

    # optional arguments
    parser.add_argument(
        "-n",
        dest="nup",
        metavar="N",
        action="store",
        type=int,
        default="2",
        help="Pages per sheet (default: 2)",
    )
    parser.add_argument(
        "-f",
        dest="paperformat",
        action="store",
        type=str.lower,
        metavar="FORMAT",
        help="Output paper sheet format. Must be standard"
        " paper format (A4, letter, ...) or custom"
        " WIDTHxHEIGHT (default: auto)",
    )
    parser.add_argument(
        "-u",
        dest="unit",
        action="store",
        default="mm",
        choices=["cm", "inch", "mm"],
        help="Unit if using -f with custom format" " (default: mm)",
    )
    parser.add_argument(
        "-b",
        dest="binding",
        action="store",
        type=str.lower,
        choices=["left", "top", "right", "bottom"],
        default="left",
        help="Side of binding (default: left)",
    )
    parser.add_argument(
        "-c",
        dest="center_subpage",
        action="store_true",
        help="Center each page when resizing. Has no effect if"
        " output format is multiple of input format (default:"
        " center combinated pages)",
    )
    parser.add_argument(
        "-s",
        dest="signature_length",
        action="store",
        type=int,
        default=-1,
        help="Signature length. Set to 0 to disable " "signatures (default: auto)",
    )
    parser.add_argument(
        "-d",
        dest="divider",
        action="store_true",
        default=False,
        help="Insert blank sheets between signature stacks to"
        " ease separation after printing",
    )
    parser.add_argument(
        "-v", dest="verbose", action="store_true", default=False, help="Verbose output"
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s {}".format(__version__)
    )

    return parser.parse_args()


def main() -> None:
    args: Namespace = parse_arguments()

    # validate cli arguments
    infile: str = core.validate_infile(args.PDF)
    signature_length: int = core.validate_signature_length(args.signature_length)
    papersize: Dict[str, List[int]] = core.validate_papersize(
        args.paperformat, args.unit
    )
    pages_per_sheet: int = core.validate_pages_per_sheet(args.nup)

    # read pdf file
    inpages: List = PdfReader(infile).pages

    page_count: int = len(inpages)

    # calculate signature length, if not set manually through cli argument
    if signature_length == 0:
        # signatures are disabled, just pad to multiple of 4
        signature_length = page_count + core.reverse_remainder(page_count, 4)
    if signature_length < 0:
        # calculate signature length
        signature_length = core.calculate_signature_length(page_count)

    signature_count: int = math.ceil(page_count / signature_length)

    # pad with blank pages
    blank_pages_count: int = signature_length * signature_count - page_count
    if blank_pages_count:
        inpages.extend([core.create_blank_copy(inpages[0])] * blank_pages_count)

    # calculate output size of single page for centering content
    output_size: List[int] = None
    if papersize and args.center_subpage:
        output_size = core.calculate_scaled_sub_page_size(pages_per_sheet, papersize)

    # impose and merge pages, creating sheets
    sheets: List = core.impose_and_merge(
        inpages, signature_length, pages_per_sheet, output_size, args.binding
    )

    # add divider pages
    if args.divider:
        sheets = core.add_divider(sheets, signature_length)

    # resize result
    if papersize:
        sheets = core.resize(sheets, papersize)

    # print infos
    if args.verbose:
        for line in textwrap.wrap(
            "Standard paper formats: {}".format(
                ", ".join(sorted(core.paperformats.keys()))
            ),
            80,
        ):
            print(line)

        print("Total input page:  {:>3}".format(page_count))
        print("Total output page: {:>3}".format(len(sheets)))

        input_size = inpages[0].MediaBox[2:]
        output_size = sheets[0].MediaBox[2:]
        divider_count = 2 * signature_count - 2 if args.divider else 0

        print("Input size:        {}x{}".format(input_size[0], input_size[1]))
        print("Output size:       {}x{}".format(output_size[0], output_size[1]))
        print("Signature length:  {:>3}".format(signature_length))
        print("Signature count:   {:>3}".format(signature_count))
        print("Divider pages:     {:>3}".format(divider_count))

    # save imposed pdf
    core.save_pdf(infile, sheets)
    print("Imposed PDF file saved to {}".format(core.create_filename(infile)))


if __name__ == "__main__":
    exit(main())
