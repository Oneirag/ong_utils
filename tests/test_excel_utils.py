"""
Tests of the excel module of ong_utils
"""
import os
import unittest

import numpy as np
import pandas as pd

from ong_utils.excel import df_to_excel


class TestExcelUtils(unittest.TestCase):
    test_file = "test_file.xlsx"
    test_sheet = "test"

    def delete_test_file(self):
        if os.path.isfile(self.test_file):
            os.remove(self.test_file)

    def test_df_to_excel(self):
        """Tests that a random pandas dataframe is properly saved"""
        # One df with strings as column names and the other with integers
        dfs = [
            pd.DataFrame(np.random.randint(0, 100, size=(100, 4)), columns=list('ABCD')),
            pd.DataFrame(np.random.randint(0, 100, size=(100, 4)))
        ]

        for df in dfs:
            with self.subTest(df=df):
                self.delete_test_file()
                with pd.ExcelWriter(self.test_file, engine="openpyxl") as xlsx:
                    df_to_excel(df, xlsx, sheet_name=self.test_sheet)
                self.assertTrue(os.path.isfile(self.test_file), "Test file was not created")
                self.delete_test_file()


if __name__ == '__main__':
    unittest.main()
