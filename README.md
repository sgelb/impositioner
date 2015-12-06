## impositioner

A simple script for impositioning PDF files for booklet printing.

### Features

- simple to print and sort
- automatically or manually setting of signatures
- N-up printing of multiple sheets on a page
- binding on any side
- option to set output size

### Options

```sh
usage: impositioner.py [-h] [-n N] [-f FORMAT] [-u {cm,inch,mm}]
                       [-b {left,top,right,bottom}] [-c] [-s SIGNATURELENGTH]
                       PDF

Impose PDF file for booklet printing

positional arguments:
  PDF                   PDF file

optional arguments:
  -h, --help            show this help message and exit
  -n N                  Pages per sheet (default: 2)
  -f FORMAT             Output paper format. Must be standard paper format
                        (A4, letter, ...) or custom WIDTHxHEIGHT (default:
                        auto)
  -u {cm,inch,mm}       Unit if using -f with custom format (default: mm)
  -b {left,top,right,bottom}
                        Side of binding (default: left)
  -c                    Center each page when resizing. Has no effect if
                        output format is multiple of input format (default:
                        center combinated pages)
  -s SIGNATURELENGTH    Signature length. Set to 0 to disable signatures
                        (default: auto)

Examples:

Print 4 pages on A4, creating an A6 booklet:
$ ./impositioner.py -n 4 -f a4 input.pdf

Create booklet with binding on right side and signatures of 20 pages:
$ ./impositioner.py -b right -s 20 input.pdf

Create booklet with custom output format. Center each page before
combining:
$ ./impositioner.py -f 209.5x209.5 input.pdf
```


### Printing

This depends on your printer. This is how I print on my Samsung printer without
duplex function:

1. Print all odd pages.
2. Put printed pages back. I have to rotate them 180°.
3. Print all even pages in reversed order.
