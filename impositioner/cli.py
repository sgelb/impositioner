#!/usr/bin/env python
"""
Main entry point for command-line program, invoke as `impositioner'
"""

import math
import textwrap
from argparse import Action, ArgumentParser, RawDescriptionHelpFormatter
from dataclasses import dataclass
from sys import exit
from typing import List, Optional

from pdfrw import PdfReader

from . import __version__, core


@dataclass
class Arguments:
    pdf: str
    nup: int = 2
    paperformat: Optional[str] = None
    unit: str = "mm"
    binding: str = "left"
    center_subpage: bool = False
    signature_length: int = -1
    outfolder: str = "./"
    divider: bool = False
    verbose: bool = False


class ListPaperFormatsAction(Action):
    def __init__(self, option_strings, dest, help):
        super().__init__(option_strings=option_strings, dest=dest, const=True, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if self.const:
            print("Supported paper formats:")
            print(", ".join(sorted(core.paperformats.keys())))
            parser.exit()


def parse_arguments() -> Arguments:
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

        4 pages on an A4 sheet for creating an A6 booklet:
        $ %(prog)s -n 4 -f a4 input.pdf

        Binding on right side and signatures of 20 pages:
        $ %(prog)s -b right -s 20 input.pdf

        Use custom output format and center each page before combining:
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
        help="pages per sheet (default: 2)",
    )
    parser.add_argument(
        "-f",
        dest="paperformat",
        action="store",
        type=str.lower,
        metavar="FORMAT",
        help=(
            "output paper sheet format. Must be standard"
            " paper format (A4, letter, ...) or custom"
            " WIDTHxHEIGHT (default: auto)"
        ),
    )
    parser.add_argument(
        "-o",
        dest="outfolder",
        action="store",
        type=str,
        default="./",
        help="folder where impositioned pdf file are saved (default: current folder)",
    )
    parser.add_argument(
        "-u",
        dest="unit",
        action="store",
        default="mm",
        choices=["cm", "inch", "mm"],
        help="unit if using -f with custom format (default: mm)",
    )
    parser.add_argument(
        "-b",
        dest="binding",
        action="store",
        type=str.lower,
        choices=["left", "top", "right", "bottom"],
        default="left",
        help="side of binding (default: left)",
    )
    parser.add_argument(
        "-c",
        dest="center_subpage",
        action="store_true",
        help=(
            "center each page when resizing. Has no effect if output format is multiple of input format (default:"
            " center combinated pages)"
        ),
    )
    parser.add_argument(
        "-s",
        dest="signature_length",
        action="store",
        type=int,
        default=-1,
        help="signature length. Set to 0 to disable signatures (default: set automatically)",
    )
    parser.add_argument(
        "-d",
        dest="divider",
        action="store_true",
        help="insert blank sheets between signature stacks to ease separation after printing",
    )
    parser.add_argument("-v", dest="verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--list-formats",
        dest="list_formats",
        action=ListPaperFormatsAction,
        help="list standard paper formats supported by -f and exit",
    )
    parser.add_argument("--version", action="version", version="%(prog)s {}".format(__version__))

    args = parser.parse_args()
    return Arguments(
        pdf=args.PDF,
        nup=args.nup,
        paperformat=args.paperformat,
        unit=args.unit,
        binding=args.binding,
        center_subpage=args.center_subpage,
        signature_length=args.signature_length,
        outfolder=args.outfolder,
        divider=args.divider,
        verbose=args.verbose,
    )


def run(args: Arguments) -> None:
    # validate arguments
    infile: str = core.validate_infile(args.pdf)
    signature_length: int = core.validate_signature_length(args.signature_length)
    papersize: Optional[List[int]] = core.validate_papersize(args.paperformat, args.unit)
    pages_per_sheet: int = core.validate_pages_per_sheet(args.nup)
    center_subpage = args.center_subpage
    binding = args.binding
    divider = args.divider
    outfolder = args.outfolder
    verbose = args.verbose

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
    output_size: Optional[List[int]] = None
    if papersize and center_subpage:
        output_size = core.calculate_scaled_sub_page_size(pages_per_sheet, papersize)

    # impose and merge pages, creating sheets
    sheets: List = core.impose_and_merge(inpages, signature_length, pages_per_sheet, output_size, binding)

    # add divider pages
    if divider:
        sheets = core.add_divider(sheets, signature_length)

    # resize result
    if papersize:
        sheets = core.resize(sheets, papersize)

    # print infos
    if verbose:
        for line in textwrap.wrap(
            "Standard paper formats: {}".format(", ".join(sorted(core.paperformats.keys()))),
            80,
        ):
            print(line)

        print("Total input page:  {:>3}".format(page_count))
        print("Total output page: {:>3}".format(len(sheets)))

        input_size = inpages[0].MediaBox[2:]
        output_size = sheets[0].MediaBox[2:]
        divider_count = 2 * signature_count - 2 if divider else 0

        print("Input size:        {}x{}".format(input_size[0], input_size[1]))
        print("Output size:       {}x{}".format(output_size[0], output_size[1]))
        print("Signature length:  {:>3}".format(signature_length))
        print("Signature count:   {:>3}".format(signature_count))
        print("Divider pages:     {:>3}".format(divider_count))

    # save imposed pdf
    core.save_pdf(infile, sheets, outfolder)
    print("Imposed PDF file saved to {}".format(core.create_outfile(infile, outfolder)))


def main():
    return run(args=parse_arguments())


if __name__ == "__main__":
    exit(main())
