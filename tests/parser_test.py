import unittest
import os
import app.utils.parser as Parser

class ParserTest(unittest.TestCase):

    def setUp(self) -> None:
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, './appl_candN_2223.xlsx')
        self.df = Parser.csv_to_df(filename, False)
        return super().setUp()
        
    def test_empty_rows_are_dropped(self) -> None:
        cnt = 0
        _df = Parser.drop_empty_rows(self.df)

        # Check if drop_columns are dropped in the df
        check = [column in _df.columns for column in Parser.drop_columns]
        self.assertIsNone((filter(None, check)))
        
        # No row filled with null values exist
        self.assertIsNone(_df.iloc[_df[(_df.isnull().sum(axis=1) >= len(_df.columns.tolist()))].index])

        # Indicies are reordered properly
        for _, row in _df.itertuples():
            self.assertEqual(row.Index, cnt)
            cnt += 1

    def test_columns_are_added(self) -> None:
        _df = Parser.add_columns(self.df, file_version=0)
        df_columns = _df.columns.values.tolist()
        # Check if the columns of the df match the keys of the column map
        self.assertEqual(list(Parser.col_names_map.values()).sort(), df_columns.sort())
        # Version is inserted properly
        self.assertEqual(_df['version'].sum(), 0)


    def test_null_values_are_filled(self) -> None:
        _df = Parser.fill_null_values(self.df)
        self.assertIsNone(_df['First Name'].isnull())
        self.assertIsNone(_df['Last Name'].isnull())
        self.assertIsNone(_df['Email'].isnull())
        self.assertIsNone(_df['Admissions Cycle'].isnull())


    def test_erpids_are_inserted(self, df) -> None:
        _df = self.insert_erpid(self.df)
        self.assertIsNone(_df['Erpid'].isnull())

    def test_missing_program_codes_are_handled():
        pass

    def tearDown(self) -> None:
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()