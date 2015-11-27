## Impositioner

Basic imposition of PDF files

### Features

- simple to print and sort
- automatic or manual setting of signature length
- n-up imposition, e.g for printing an A6 booklet on A4 paper

### Usage

```
usage: impositioner.py [-h] [-n NUP] [-f FORMAT] [-u {cm,inch,mm}] [-c]
                       [-s SIGNATURELENGTH]
                       PDF

Impose PDF file

positional arguments:
  PDF                 PDF file

optional arguments:
  -h, --help          show this help message and exit
  -n NUP              pages per sheet (default: 2)
  -f FORMAT           Set output paper format. Must be standard paper format
                      (A4, letter, ...) or WIDTHxHEIGHT (default: auto)
  -u {cm,inch,mm}     Unit for custom output format (default: mm)
  -c                  Center each page when resizing
  -s SIGNATURELENGTH  Set signature length (default: auto)
```

### Todo

- [x] basic imposing
- [x] signatures
- [x] set output size
  - [x] standard papersizes: A0 - A8, letter, ...
  - [x] scaling
  - [x] scale and center each single page instead of result. make it an option
- [x] support for landscape input
- [x] add license
- [ ] support folding on short edge
- [ ] user defined output
  - [x] custom output size
  - [ ] custom layout, e.g. 1x3, allowing whitespace
- [ ] more usage infos, explanation of cli options and examples
- [ ] illustrated help for folding/cutting
- [ ] add front- and/or backcover from extra pdf file
- [ ] add blank pages for easy separation of signatures after printing

### Maybe

- [ ] better name
- [ ] support rtl/fold on right side
- [ ] double/parallel print
- [ ] add cut line
- [ ] creep/shingling/push out
