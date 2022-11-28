import unittest
import os
import copy
import app.utils.parser as Parser
from app.models.applicant import Program


class ParserTest(unittest.TestCase):

    def setUp(self) -> None:
        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'appl_candN_2223.xlsx')
        self.df = Parser.csv_to_df(filename, False)
        

    def test_empty_rows_are_dropped(self) -> None:
        cnt = 0
        _df = copy.copy(self.df)
        Parser.drop_empty_rows(_df)

        # Check if drop_columns are dropped in the df
        check = [column in _df.columns for column in Parser.drop_columns]
        check = [column for column in check if column]
        self.assertEqual(len(check), 0)
        
        # No row filled with null values exist
        self.assertEqual(len(_df.iloc[_df[(_df.isnull().sum(axis=1) >= len(_df.columns.tolist()))].index]), 0)

        # Indicies are reordered properly
        for row in _df.itertuples():
            self.assertEqual(row.Index, cnt)
            cnt += 1


    def test_columns_are_added(self) -> None:
        _df = copy.copy(self.df)
        Parser.add_columns(_df, file_version=0)
        df_columns = _df.columns.values.tolist()

        # Check if the columns of the df match the keys of the column map
        self.assertEqual(list(Parser.col_names_map.values()).sort(), df_columns.sort())

        # Version is inserted properly
        self.assertEqual(_df['version'].sum(), 0)


    def test_null_values_are_filled(self) -> None:
        _df = copy.copy(self.df)
        Parser.drop_empty_rows(_df)
        Parser.add_columns(_df, 0)
        Parser.fill_null_values(_df)
        self.assertFalse(_df['First Name'].isnull().any())
        self.assertFalse(_df['Last Name'].isnull().any())
        self.assertFalse(_df['Email'].isnull().any())
        self.assertFalse(_df['Admissions Cycle'].isnull().any())


    def test_erpids_are_inserted(self) -> None:
        _df = copy.copy(self.df)
        Parser.insert_erpid(_df)
        erpid_is_null = _df[_df['Erpid'].isnull()]
        self.assertEqual(len(erpid_is_null), 0)


    # def test_missing_program_codes_are_handled(self) -> None:
    #     _df = copy.copy(self.df)
    #     Parser.insert_missing_program_codes(_df)
    #     program_codes = list(map(lambda x: x.code, Program.query.all()))
    #     for code in _df["Programme Code"].tolist():
    #         self.assertIn(code, program_codes)

    def tearDown(self) -> None:
        pass

if __name__ == '__main__':
    unittest.main()