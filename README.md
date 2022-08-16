## impositioner

A simple script for impositioning PDF files for booklet printing.

### Features

- simple to print and sort
- automatically or manually setting of signatures
- N-up printing of multiple pages on a sheet
- binding on any side
- option to set output size

### Options

```
usage: impositioner [-h] [-n N] [-f FORMAT] [-u {cm,inch,mm}]
                    [-b {left,top,right,bottom}] [-c] [-s SIGNATURE_LENGTH]
                    [-d] [-v]
                    PDF

Impose PDF file for booklet printing

positional arguments:
  PDF                   PDF file

optional arguments:
  -h, --help            show this help message and exit
  -n N                  Pages per sheet (default: 2)
  -f FORMAT             Output paper sheet format. Must be standard paper
                        format (A4, letter, ...) or custom WIDTHxHEIGHT
                        (default: auto)
  -u {cm,inch,mm}       Unit if using -f with custom format (default: mm)
  -b {left,top,right,bottom}
                        Side of binding (default: left)
  -c                    Center each page when resizing. Has no effect if
                        output format is multiple of input format (default:
                        center combinated pages)
  -s SIGNATURE_LENGTH   Signature length. Set to 0 to disable signatures
                        (default: auto)
  -d                    Insert blank sheets between signature stacks to ease
                        separation after printing
  -v                    Verbose output

Examples:

Print 4 pages on an A4 sheet for creating an A6 booklet:
$ impositioner -n 4 -f a4 input.pdf

Create booklet with binding on right side and signatures of 20 pages:
$ impositioner -b right -s 20 input.pdf

Create booklet with custom output format. Center each page before
combining:
$ impositioner -f 209.5x209.5 -c input.pdf
```

### Development and Installation

This project uses [Poetry](https://python-poetry.org/) for dependency managment. There is also a
simple `Makefile` with some convenience commands.

You can use `tools/pdfSampler.py` to create sample pdfs:

```
usage: pdfSampler.py [-h] [--landscape] [--bbox] pages format

Create sample PDF file with specified number of pages and format

positional arguments:
  pages            number of pages
  format           standard paper format like A4, letter,

options:
  -h, --help       show this help message and exit
  --landscape, -l  output in landscape (default: portrait)
  --bbox, -b       draw bbox
```

### Printing

This depends on your printer. This is how I print on my Samsung printer without duplex function:

1. Print all odd pages.
2. Put printed pages back. I have to rotate them 180°.
3. Print all even pages in reversed order.
