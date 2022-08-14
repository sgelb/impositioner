import hashlib
import os
import shutil
import unittest
from tempfile import TemporaryDirectory

from .context import cli, core


def md5sum(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            hash.update(block)
    return hash.hexdigest()


class test_pdf(unittest.TestCase):
    def setUp(self):
        self.testfiles = {
            os.path.abspath("tests/a5_portrait_20.pdf"): "930eef35aed350e7082edc9be07c1331",
            os.path.abspath("tests/a5_landscape_20.pdf"): "0e4942d591ac854fe37b18e65fef4af9",
        }

    def tearDown(self):
        pass

    def testImpositioning(self):
        with TemporaryDirectory() as d:
            for fn, hash in self.testfiles.items():
                shutil.copy(fn, d)
                testfile = os.path.join(d, os.path.basename(fn))
                bookletfile = core.outfile(d, fn)
                args = cli.Arguments(pdf=testfile, outfolder=d)
                cli.run(args)
                self.assertEqual(md5sum(bookletfile), hash)
