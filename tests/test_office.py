import os.path
import time
import unittest
from typing import Type

from ong_utils.office.office_base import AccessBase, PowerpointBase, ExcelBase, WordBase, _OfficeBase


class TestOfficeBaseClasses(unittest.TestCase):
    test_dir = "test_files"

    def get_sample_filename(self, sample_filename: str) -> str:
        """Gets full path of a sample filename"""
        base_dir = os.path.join(os.path.dirname(__file__), self.test_dir)
        sample_file = os.path.join(base_dir, sample_filename)
        if os.path.isfile(sample_file):
            return sample_file
        raise FileNotFoundError(f"Could not open {sample_file}")

    def open_file(self, class_: Type[_OfficeBase], sample_filename: str):
        for filename in self.get_sample_filename(sample_filename), os.path.join(self.test_dir, sample_filename):
            with self.subTest(filename=filename):
                obj = class_()
                obj.open(filename)
                time.sleep(2)
                obj.quit()

    def test_excel_base(self):
        """Tests that a xlsx opens and closes properly without exceptions"""
        self.open_file(ExcelBase, "excel_sample.xlsx")

    def test_word_base(self):
        """Tests that a docx opens and closes properly without exceptions"""
        self.open_file(WordBase, "word_sample.docx")

    def test_powerpoint_base(self):
        """Tests that a ppt file opens and closes properly without exceptions"""
        self.open_file(PowerpointBase, "powerpoint_sample.pptx")

    def test_access_base(self):
        """Tests that an accdb file opens and closes properly without exceptions"""
        self.open_file(AccessBase, "access_sample.accdb")


if __name__ == '__main__':
    unittest.main()
