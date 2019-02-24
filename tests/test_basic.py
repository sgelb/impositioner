from pdfrw import PdfReader, PageMerge
import os
import unittest

from .context import core


# class test_cli(unittest.TestCase):

#     def test_parse_arguments(self):
#         pass


# class test_gui(unittest.TestCase):
# pass


class test_core(unittest.TestCase):
    def setUp(self):
        portrait_file = os.path.abspath("tests/a5_portrait_20.pdf")
        landscape_file = os.path.abspath("tests/a5_landscape_20.pdf")
        self.portrait_pdf = PdfReader(portrait_file).pages
        self.landscape_pdf = PdfReader(landscape_file).pages

    def tearDown(self):
        self.pages = None

    def test_reverse_remainder(self):
        self.assertEqual(core.reverse_remainder(13, 3), 2)
        self.assertNotEqual(core.reverse_remainder(13, 3), 3)
        self.assertEqual(core.reverse_remainder(12, 3), 0)
        self.assertEqual(core.reverse_remainder(3, 4), 1)
        self.assertEqual(core.reverse_remainder(0, 4), 0)
        with self.assertRaises(ZeroDivisionError):
            core.reverse_remainder(3, 0)

    def test_calculate_signature(self):
        self.assertEqual(core.calculate_signature_length(-1), 0)
        self.assertEqual(core.calculate_signature_length(0), 0)
        self.assertEqual(core.calculate_signature_length(3), 4)
        self.assertEqual(core.calculate_signature_length(32), 32)
        self.assertEqual(core.calculate_signature_length(34), 36)
        self.assertEqual(core.calculate_signature_length(36), 36)
        self.assertEqual(core.calculate_signature_length(37), 20)
        self.assertEqual(core.calculate_signature_length(46), 24)
        self.assertEqual(core.calculate_signature_length(53), 28)
        self.assertEqual(core.calculate_signature_length(61), 32)
        self.assertEqual(core.calculate_signature_length(65), 36)

    def test_cut_in_signatures(self):
        self.assertEqual(
            list(core.cut_in_signatures([1, 2, 3, 4], 2)), [[1, 2], [3, 4]]
        )
        self.assertEqual(list(core.cut_in_signatures([1, 2, 3, 4], 4)), [[1, 2, 3, 4]])
        self.assertEqual(
            list(core.cut_in_signatures([1, 2, 3, 4], 1)), [[1], [2], [3], [4]]
        )
        self.assertEqual(
            list(core.cut_in_signatures([1, 2, 3, 4], 3)), [[1, 2, 3], [4]]
        )

    def test_calculate_scaled_sub_page_size(self):
        self.assertEqual(
            core.calculate_scaled_sub_page_size(2, core.paperformats["a5"]), [298, 420]
        )
        self.assertEqual(
            core.calculate_scaled_sub_page_size(4, core.paperformats["a5"]), [210, 298]
        )
        self.assertEqual(
            core.calculate_scaled_sub_page_size(2, core.paperformats["a4"]), [421, 595]
        )
        self.assertEqual(
            core.calculate_scaled_sub_page_size(8, core.paperformats["a4"]), [298, 210]
        )

    def test_add_blanks(self):
        with self.assertRaises(ZeroDivisionError):
            core.add_blanks(self.portrait_pdf, 0)

        self.assertEqual(core.add_blanks(self.portrait_pdf, 2), self.portrait_pdf)

        blank = core.create_blank_copy(self.portrait_pdf[0])
        result = core.add_blanks(self.portrait_pdf, 4)
        self.assertEqual(len(result), len(self.portrait_pdf) + 4)

        self.assertEqual(result[9], self.portrait_pdf[9])
        self.assertEqual(result[12], self.portrait_pdf[10])

        for i in [-1, -2, 10, 11]:
            self.assertEqual(result[i], blank)

    def test_get_media_box_size(self):
        self.assertEqual(core.get_media_box_size(self.portrait_pdf), [420, 595])
        self.assertEqual(core.get_media_box_size(self.landscape_pdf), [595, 420])

        pages = list(self.portrait_pdf)
        pages[0].Rotate = 90
        self.assertEqual(core.get_media_box_size(pages), [595, 420])

        pages[0].Rotate = 180
        self.assertEqual(core.get_media_box_size(pages), [420, 595])

        pages[0].Rotate = 270
        self.assertEqual(core.get_media_box_size(pages), [595, 420])

    def test_calculate_margins(self):
        self.assertEqual(core.calculate_margins([80, 80], [8, 8]), (10, 0, 0))
        self.assertEqual(core.calculate_margins([50, 80], [50, 10]), (1, 0, 35))
        self.assertEqual(core.calculate_margins([80, 50], [10, 50]), (1, 35, 0))
        with self.assertRaises(ZeroDivisionError):
            core.calculate_margins([1, 1], [0, 1])
        with self.assertRaises(ZeroDivisionError):
            core.calculate_margins([1, 1], [1, 0])

    def test_resize(self):
        with self.assertRaises(ZeroDivisionError):
            core.resize(self.portrait_pdf, [10, 0])

        for fmt in (f for f in core.paperformats.keys() if f != "ledger"):
            resized = core.resize(self.portrait_pdf, core.paperformats[fmt])
            self.assertEqual(resized[0].MediaBox[2:], core.paperformats[fmt])

        for fmt in (f for f in core.paperformats.keys() if f != "ledger"):
            resized = core.resize(self.landscape_pdf, core.paperformats[fmt])
            self.assertEqual(
                resized[0].MediaBox[2:], list(reversed(core.paperformats[fmt]))
            )

        # ledger is the only landscape format, so test it extra
        resized = core.resize(self.portrait_pdf, core.paperformats["ledger"])
        self.assertEqual(
            resized[0].MediaBox[2:], list(reversed(core.paperformats["ledger"]))
        )

        resized = core.resize(self.landscape_pdf, core.paperformats["ledger"])
        self.assertEqual(resized[0].MediaBox[2:], core.paperformats["ledger"])

        resized = core.resize(self.portrait_pdf, [10, 10])
        self.assertEqual(resized[0].MediaBox[2:], [10, 10])

    def test_is_landscape(self):
        page = PageMerge() + self.portrait_pdf[0]
        self.assertFalse(core.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertTrue(core.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertFalse(core.is_landscape(page))

        page.rotate = 90
        page = PageMerge() + page.render()
        self.assertTrue(core.is_landscape(page))

        page = PageMerge() + self.landscape_pdf[0]
        self.assertTrue(core.is_landscape(page))

    def test_validate_infile(self):
        with self.assertRaises(SystemExit):
            core.validate_infile("not_exisiting.pdf")

    def test_validate_papersize(self):
        self.assertEqual(core.validate_papersize(None, "mm"), None)
        self.assertEqual(core.validate_papersize("a5", "mm"), core.paperformats["a5"])
        self.assertEqual(core.validate_papersize("17.5x200", "mm"), [50, 567])
        self.assertEqual(core.validate_papersize("17.50x200.000", "mm"), [50, 567])
        self.assertEqual(core.validate_papersize(".50x10", "cm"), [14, 283])
        self.assertEqual(core.validate_papersize(".50X10", "cm"), [14, 283])
        with self.assertRaises(SystemExit):
            core.validate_papersize("-17.5x200", "mm")
        with self.assertRaises(SystemExit):
            core.validate_papersize("17.5x-200", "mm")
        with self.assertRaises(SystemExit):
            core.validate_papersize(".x200", "mm")

    def test_validate_pages_per_sheet(self):
        self.assertEqual(core.validate_pages_per_sheet(2), 2)
        self.assertEqual(core.validate_pages_per_sheet(4), 4)
        self.assertEqual(core.validate_pages_per_sheet(8), 8)
        self.assertEqual(core.validate_pages_per_sheet(16), 16)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(1)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(0)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(-1)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(3)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(6)
        with self.assertRaises(SystemExit):
            core.validate_pages_per_sheet(12)

    def test_validate_signature_length(self):
        self.assertEqual(core.validate_signature_length(4), 4)
        self.assertEqual(core.validate_signature_length(8), 8)
        self.assertEqual(core.validate_signature_length(40), 40)
        self.assertEqual(core.validate_signature_length(-1), -1)
        with self.assertRaises(SystemExit):
            core.validate_signature_length(1)
        with self.assertRaises(SystemExit):
            core.validate_signature_length(2)
        with self.assertRaises(SystemExit):
            core.validate_signature_length(3)
        with self.assertRaises(SystemExit):
            core.validate_signature_length(5)
        with self.assertRaises(TypeError):
            core.validate_signature_length("A")

    def test_create_filename(self):
        self.assertEqual(core.create_filename("foo/bar.tmp"), "booklet.bar.tmp")
        self.assertEqual(core.create_filename("/foo/bar.tmp"), "booklet.bar.tmp")
        self.assertEqual(core.create_filename("~/bar.tmp"), "booklet.bar.tmp")

    def test_add_divider(self):
        blank_page = core.create_blank_copy(self.portrait_pdf[0])
        self.assertNotEqual(self.portrait_pdf[10], blank_page)

        divided_pages = core.add_divider(self.portrait_pdf, 10)

        self.assertEqual(divided_pages[7], self.portrait_pdf[5])
        self.assertEqual(divided_pages[14], self.portrait_pdf[10])

        self.assertEqual(divided_pages[5], blank_page)
        self.assertEqual(divided_pages[6], blank_page)
        self.assertEqual(divided_pages[10], blank_page)
        self.assertEqual(divided_pages[11], blank_page)

    # def test_impose(self):
    #     pass

    # def test_merge(self):
    #     pass

    # def test_impose_and_merge(self):
    #     pass

    # def test_save_pdf(self):
    #     pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
