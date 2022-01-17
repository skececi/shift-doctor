from googlesheets.helpers import letter_from_num


class InputRange:
    def __init__(self, sheet_name, start_row, start_col, end_row, end_col):
        self.sheet_name = sheet_name
        self.start_row = start_row
        self.start_col = start_col
        self.end_row = end_row
        self.end_col = end_col

    def to_range_string(self):
        return self.sheet_name + '!' + letter_from_num(self.start_col) + str(self.start_row) + ':' \
               + letter_from_num(self.end_col) + str(self.end_row)
