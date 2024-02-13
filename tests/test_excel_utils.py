"""
Tests of the Excel module of ong_utils.
Also adds sensitivity labels to the created files, based on the Excel file of the test_files folder
"""
import os
import unittest

import numpy as np
import pandas as pd

from ong_utils.excel import df_to_excel
from ong_utils import SensitivityLabel


class TestExcelUtils(unittest.TestCase):
    test_file = "test_file.xlsx"
    test_sheet = "test"

    def delete_test_file(self):
        if os.path.isfile(self.test_file):
            os.remove(self.test_file)

    def setUp(self):
        # One df with strings as column names and the other with integers
        self.dfs = [
            pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')),
            pd.DataFrame(np.random.randint(0, 100, size=(100, 4)))
        ]
        sample_excel = os.path.join(os.path.dirname(__file__), "test_files", "excel_sample.xlsx")
        self.sensitivity_label = SensitivityLabel(sample_excel)
        self.delete_test_file()

    def test_write_xlsx(self):
        """Tests that Excel sheets can be written (correct libraries are installed)"""
        for df in self.dfs:
            with self.subTest(df=df):
                with pd.ExcelWriter(self.test_file) as xlsx:
                    print(f"Writing {self.test_file} using engine={xlsx.engine}")
                    df.to_excel(xlsx, sheet_name=self.test_sheet)
                self.sensitivity_label.apply(self.test_file)
                self.assertTrue(os.path.isfile(self.test_file), "No file created")
                self.delete_test_file()

    def test_df_to_excel(self):
        """Tests that a random pandas dataframe is properly saved"""
        for df in self.dfs:
            with self.subTest(df=df):
                self.delete_test_file()
                with pd.ExcelWriter(self.test_file, engine="openpyxl") as xlsx:
                    df_to_excel(df, xlsx, sheet_name=self.test_sheet)
                self.sensitivity_label.apply(self.test_file)
                self.assertTrue(os.path.isfile(self.test_file), "Test file was not created")
                self.delete_test_file()


if __name__ == '__main__':
    unittest.main()
