from .context import impositioner as imp
from pdfrw import PdfReader, PageMerge
import os

import unittest


class test_impositioner(unittest.TestCase):

    def setUp(self):
        testfile = os.path.abspath("tests/a5_portrait_20.pdf")
        self.pages = PdfReader(testfile).pages

    def tearDown(self):
        self.pages = None

    def test_reverse_remainder(self):
        self.assertEqual(imp.reverse_remainder(13, 3), 2)
        self.assertNotEqual(imp.reverse_remainder(13, 3), 3)
        self.assertEqual(imp.reverse_remainder(12, 3), 0)
        self.assertEqual(imp.reverse_remainder(3, 4), 1)
        self.assertEqual(imp.reverse_remainder(0, 4), 0)
        with self.assertRaises(ZeroDivisionError):
            imp.reverse_remainder(3, 0)

    def test_calculate_signature(self):
        self.assertEqual(imp.calculate_signature_length(-1), 0)
        self.assertEqual(imp.calculate_signature_length(0), 0)
        self.assertEqual(imp.calculate_signature_length(3), 4)
        self.assertEqual(imp.calculate_signature_length(32), 32)
        self.assertEqual(imp.calculate_signature_length(34), 36)
        self.assertEqual(imp.calculate_signature_length(36), 36)
        self.assertEqual(imp.calculate_signature_length(37), 20)
        self.assertEqual(imp.calculate_signature_length(46), 24)
        self.assertEqual(imp.calculate_signature_length(53), 28)
        self.assertEqual(imp.calculate_signature_length(61), 32)
        self.assertEqual(imp.calculate_signature_length(65), 36)

    def test_cut_in_signatures(self):
        self.assertEqual(list(imp.cut_in_signatures([1, 2, 3, 4], 2)),
                         [[1, 2], [3, 4]])
        self.assertEqual(list(imp.cut_in_signatures([1, 2, 3, 4], 4)),
                         [[1, 2, 3, 4]])
        self.assertEqual(list(imp.cut_in_signatures([1, 2, 3, 4], 1)),
                         [[1], [2], [3], [4]])
        self.assertEqual(list(imp.cut_in_signatures([1, 2, 3, 4], 3)),
                         [[1, 2, 3], [4]])

    def test_calculate_scaled_sub_page_size(self):
        self.assertEqual(
            imp.calculate_scaled_sub_page_size(2, imp.paperformats["a5"]),
            [298, 420])
        self.assertEqual(
            imp.calculate_scaled_sub_page_size(4, imp.paperformats["a5"]),
            [210, 298])
        self.assertEqual(
            imp.calculate_scaled_sub_page_size(2, imp.paperformats["a4"]),
            [421, 595])
        self.assertEqual(
            imp.calculate_scaled_sub_page_size(8, imp.paperformats["a4"]),
            [298, 210])

    def test_get_media_box_size(self):
        pages = self.pages
        self.assertEqual(imp.get_media_box_size(pages), [420, 595])
        pages[0].Rotate = 90
        self.assertEqual(imp.get_media_box_size(pages), [595, 420])

    def test_calculate_margins(self):
        self.assertEqual(imp.calculate_margins([80, 80], [8, 8]), (10, 0, 0))
        self.assertEqual(imp.calculate_margins([50, 80], [50, 10]), (1, 0, 35))
        self.assertEqual(imp.calculate_margins([80, 50], [10, 50]), (1, 35, 0))
        with self.assertRaises(ZeroDivisionError):
            imp.calculate_margins([1, 1], [0, 1])
        with self.assertRaises(ZeroDivisionError):
            imp.calculate_margins([1, 1], [1, 0])

    def test_is_landscape(self):
        page = PageMerge() + self.pages[0]
        self.assertFalse(imp.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertTrue(imp.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertFalse(imp.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertTrue(imp.is_landscape(page))

    def test_validate_papersize(self):
        self.assertEquals(imp.validate_papersize(None, "mm"), None)
        self.assertEquals(imp.validate_papersize("a5", "mm"),
                          imp.paperformats["a5"])
        self.assertEquals(imp.validate_papersize("17.5x200", "mm"),
                          [50, 567])
        self.assertEquals(imp.validate_papersize("17.50x200.000", "mm"),
                          [50, 567])
        self.assertEquals(imp.validate_papersize(".50x10", "cm"),
                          [14, 283])
        self.assertEquals(imp.validate_papersize(".50X10", "cm"),
                          [14, 283])
        with self.assertRaises(SystemExit):
            imp.validate_papersize("-17.5x200", "mm")
        with self.assertRaises(SystemExit):
            imp.validate_papersize("17.5x-200", "mm")
        with self.assertRaises(SystemExit):
            imp.validate_papersize(".x200", "mm")

    def test_validate_pages_per_sheet(self):
        self.assertEquals(imp.validate_pages_per_sheet(2), 2)
        self.assertEquals(imp.validate_pages_per_sheet(4), 4)
        self.assertEquals(imp.validate_pages_per_sheet(8), 8)
        self.assertEquals(imp.validate_pages_per_sheet(16), 16)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(1)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(0)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(-1)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(3)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(6)
        with self.assertRaises(SystemExit):
            imp.validate_pages_per_sheet(12)

    def test_validate_signature_length(self):
        self.assertEquals(imp.validate_signature_length(4), 4)
        self.assertEquals(imp.validate_signature_length(8), 8)
        self.assertEquals(imp.validate_signature_length(40), 40)
        self.assertEquals(imp.validate_signature_length(-1), -1)
        with self.assertRaises(SystemExit):
            imp.validate_signature_length(1)
        with self.assertRaises(SystemExit):
            imp.validate_signature_length(2)
        with self.assertRaises(SystemExit):
            imp.validate_signature_length(3)
        with self.assertRaises(SystemExit):
            imp.validate_signature_length(5)
        with self.assertRaises(TypeError):
            imp.validate_signature_length("A")

    def test_create_filename(self):
        self.assertEquals(imp.create_filename("foo/bar.tmp"),
                          "booklet.bar.tmp")
        self.assertEquals(imp.create_filename("/foo/bar.tmp"),
                          "booklet.bar.tmp")
        self.assertEquals(imp.create_filename("~/bar.tmp"),
                          "booklet.bar.tmp")

    def test_add_divider(self):
        blank_page = imp.create_blank_copy(self.pages[0])
        self.assertNotEqual(self.pages[10], blank_page)

        divided_pages = imp.add_divider(self.pages, 10)

        self.assertEqual(divided_pages[7], self.pages[5])
        self.assertEqual(divided_pages[14], self.pages[10])

        self.assertEqual(divided_pages[5], blank_page)
        self.assertEqual(divided_pages[6], blank_page)
        self.assertEqual(divided_pages[10], blank_page)
        self.assertEqual(divided_pages[11], blank_page)

if __name__ == '__main__':
    unittest.main(verbosity=2)
