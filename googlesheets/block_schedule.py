from __future__ import print_function

import os.path
import pickle
from pprint import pprint

from google.auth.transport.requests import Request
# from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery

from googlesheets.constraint import RotationReq, Constraint
from googlesheets.input_range import InputRange


# TODO: better idea: just make a google account for "shift.doctor" that does everything -- easier + cleaner solution


# *** If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def auth_service():
    """Generates auth token (stored as token.pickle)
    and returns google_auth service
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = discovery.build('sheets', 'v4', credentials=creds)
    return service


def create_blank_sheet(service):
    spreadsheet_body = {
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets#Spreadsheet
    }
    request = service.spreadsheets().create(body=spreadsheet_body)
    response = request.execute()
    pprint(response['spreadsheetUrl'])
    return response


def letter_from_num(num):
    return chr(ord('@') + num)


# for rotation sums (columns) e.g. '=ArrayFormula(SUM(COUNTIFS(D$2:D$16,$A19,$B$2:$B$16, {"PGY1", "PGY2"})))'
def rotation_sum_formula(min_row, max_row, row_i, col_i, col_roles=None, roles_array_str=None):
    col_letter_i = letter_from_num(col_i)
    formula = '=ArrayFormula(SUM(COUNTIFS({col_letter_i}${min_row}:{col_letter_i}${max_row},$A{row_i})))'.format(
        min_row=min_row,
        col_letter_i=col_letter_i,
        max_row=max_row,
        row_i=row_i)
    if col_roles and roles_array_str:
        col_letter_roles = letter_from_num(col_roles)
        second_if = ',{col_letter_roles}{min_row}:{col_letter_roles}{max_row},{roles_array_str}'.format(
            col_letter_roles=col_letter_roles,
            min_row=min_row,
            max_row=max_row,
            roles_array_str=roles_array_str)
        formula = formula[:-3] + second_if + formula[-3:]
    return formula


# for doctors sums (rows) e.g. '=ArrayFormula(SUM(COUNTIFS(S$1,D3:O3)))'
def doctor_sum_formula(rotation_header_row, cur_col, cur_row, data_start_col, data_end_col):
    cur_col_letter = letter_from_num(cur_col)
    data_start_col_letter = letter_from_num(data_start_col)
    data_end_col_letter = letter_from_num(data_end_col)
    formula = '=ArrayFormula(SUM(COUNTIFS({cur_col_letter}${rotation_header_row},{data_start_col_letter}{cur_row}:{' \
        'data_end_col_letter}{cur_row})))'.format(
        cur_col_letter=cur_col_letter,
        rotation_header_row=rotation_header_row,
        data_start_col_letter=data_start_col_letter,
        data_end_col_letter=data_end_col_letter,
        cur_row=cur_row)
    return formula


def constraint_delta_formula(sum_col, sum_row, req_value):
    col_letter = letter_from_num(sum_col)
    return '={col_letter}{row} - {val}'.format(
        col_letter=col_letter,
        row=sum_row,
        val=req_value
    )


def generate_sum_row(rotation, block_length, first_col, first_doctor_row, last_doctor_row, curr_row, req=None):
    if req:
        roles = req.str_roles()
        constraint = str(req)
    else:
        roles = constraint = ''
    rotation_sum = [rotation, roles, constraint]
    for j in range(block_length):
        if req and req.roles:
            # TODO: constant
            col_roles = 2
            roles_array_str = req.roles_to_formula_array()
        else:
            col_roles = roles_array_str = None
        col_i = first_col + j
        formula = rotation_sum_formula(first_doctor_row, last_doctor_row, curr_row, col_i, col_roles, roles_array_str)
        rotation_sum.append(formula)
    return rotation_sum


def generate_doctor_sum_col(rotation, doctors_length, first_row, cur_col, req=None):
    if req:
        # roles = req.str_roles()
        constraint = str(req)
    else:
        # roles = constraint = ''
        constraint = ''
    # rotation_sum = [rotation, roles, constraint]
    rotation_sum = [rotation, constraint]
    for j in range(doctors_length):
        # if req and req.roles:
        #     roles_array_str = req.roles_to_formula_array()
        # else:
        cur_row = first_row + j
        rotation_header_row = 1
        formula = doctor_sum_formula(rotation_header_row, cur_col, cur_row, data_start_col, data_end_col-1)
        rotation_sum.append(formula)
    return rotation_sum


def build_core_schedule(service, spreadsheet_id, doctors, blocks, rotation_constraints):
    first_doctor_row = data_start_row
    last_doctor_row = first_doctor_row + len(doctors) - 1
    first_col = data_start_col
    row_gap = 3
    value_input_option = 'USER_ENTERED'
    update_range = 'Sheet1'
    header_row = [['Name', 'Roles', ''] + blocks]
    names_list = [[name, role] for name, role in doctors.items()]
    rotation_sums_list = []
    # need to generate list of lists (each inner list is a row)
    # this for loop writes the first set of summations
    curr_row = last_doctor_row + row_gap
    for rotation, req_list in rotation_constraints.items():
        if not req_list:
            rotation_sum = generate_sum_row(rotation, len(blocks), first_col, first_doctor_row, last_doctor_row,
                                            curr_row)
            rotation_sums_list.append(rotation_sum)
            curr_row += 1
        else:
            for req in req_list:
                rotation_sum = generate_sum_row(rotation, len(blocks), first_col, first_doctor_row, last_doctor_row,
                                                curr_row, req)
                rotation_sums_list.append(rotation_sum)
                curr_row += 1
    values = [[]] + header_row + names_list + [[], ['Rotation', 'Role', 'Constraint']] + rotation_sums_list
    print(values)
    body = {
        'values': values
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=update_range,
        valueInputOption=value_input_option, body=body).execute()
    print('Writing Core Table: {0} cells updated.'.format(result.get('updatedCells')))


# NOT USING CURRENTLY
def add_sum_deltas(service, spreadsheet_id, doctors, blocks, rotation_constraints):
    # TODO: make all this nonsense with rows just passed into the function
    # TODO: make all of this GLOBAL CONSTANTS
    first_doctor_row = 2
    last_doctor_row = first_doctor_row + len(doctors)
    value_input_option = 'USER_ENTERED'
    update_range = 'A:A'
    first_sum_col = 4
    first_sum_row = last_doctor_row + 1
    curr_sum_row = first_sum_row
    values = [[]]  # start with empty row
    for rotation, req in rotation_constraints.items():
        row_list = [rotation, str(req)]
        if req:
            for i in range(len(blocks)):
                curr_sum_col = first_sum_col + i
                delta_formula = constraint_delta_formula(curr_sum_col, curr_sum_row, req.value)
                row_list.append(delta_formula)
        values.append(row_list)
        curr_sum_row += 1
    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id, range=update_range,
        valueInputOption=value_input_option, body=body).execute()
    print('{0} cells appended.'.format(result
                                       .get('updates')
                                       .get('updatedCells')))


def add_conditional_format(service, spreadsheet_id, doctors, blocks, rotation_constraints):
    # TODO: could change to find this instead of hardcode
    row_gap = 1
    first_col = 4
    start_row = row_gap + len(doctors) + data_start_row
    for rotation, req_list in rotation_constraints.items():
        for req in req_list:
            ranges = [{"startRowIndex": start_row,
                       "endRowIndex": start_row + 1,
                       "startColumnIndex": first_col - 1,
                       "endColumnIndex": first_col - 1 + len(blocks)
                       }]
            condition_type = None
            if req.constraint == Constraint.EXACTLY:
                condition_type = 'NUMBER_NOT_EQ'
            elif req.constraint == Constraint.MIN:
                condition_type = 'NUMBER_LESS'
            elif req.constraint == Constraint.MAX:
                condition_type = 'NUMBER_GREATER'
            requests = [{
                'addConditionalFormatRule': {
                    'rule': {
                        'ranges': [ranges],
                        "booleanRule": {
                            "condition": {
                                "type": condition_type,
                                "values": [
                                    {
                                        "userEnteredValue": str(req.value)
                                    }
                                ]
                            },
                            "format": {
                                "backgroundColor": {
                                    "green": 50 / 256,
                                    "red": 234 / 256,
                                    "blue": 37 / 256,
                                }
                            }
                        },
                    },
                    "index": 0
                }
            }]
            body = {
                'requests': requests
            }
            response = service.spreadsheets() \
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body) \
                .execute()
            print(str(req) + ' Conditional Formatting: {0} cells updated.'.format(len(response.get('replies'))))
            start_row += 1


def add_doctor_row_constraints(service, spreadsheet_id, doctors, doctor_constraints, rotations):
    start_row = 1
    start_col = data_end_col + 2
    start_buffer = 2
    sums_start_row = start_row + start_buffer
    start_col_letter = letter_from_num(start_col)
    buffer_list = [''] * start_buffer
    value_input_option = 'USER_ENTERED'
    update_range = '{start_col_letter}1'.format(start_col_letter=start_col_letter)

    doctor_col = buffer_list + list(doctors.keys())
    training_col = buffer_list + list(doctors.values())
    doctor_sums_list = []
    # need to generate list of lists (each inner list is a row)
    # this for loop writes the first set of summations
    cur_col = start_col + 2
    for rotation, req_list in doctor_constraints.items():
        if not req_list:
            rotation_sum = generate_doctor_sum_col(rotation, len(doctors), sums_start_row, cur_col)
            doctor_sums_list.append(rotation_sum)
        else:
            for req in req_list:
                rotation_sum = generate_doctor_sum_col(rotation, len(doctors), sums_start_row, cur_col, req)
                doctor_sums_list.append(rotation_sum)
        cur_col += 1

    values = [doctor_col, training_col] + doctor_sums_list
    print(values)
    body = {
        'values': values,
        'majorDimension': 'COLUMNS'
    }
    print()
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=update_range,
        valueInputOption=value_input_option,
        body=body).execute()
    print('Writing Core Table: {0} cells updated.'.format(result.get('updatedCells')))


def add_data_validation(service, spreadsheet_id, services, start_row, end_row, start_col, end_col):
    values = []
    for rotation in services:
        values.append({'userEnteredValue': rotation})
    print(values)
    requests = [
        {
            "setDataValidation": {
                "range": {
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row - 1,
                    "startColumnIndex": start_col - 1,
                    "endColumnIndex": end_col - 1
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": values
                    },
                    "strict": True,
                    "showCustomUi": True,  # shows dropdown menu
                }
            }
        }
    ]
    body = {
        'requests': requests
    }
    response = service.spreadsheets() \
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body) \
        .execute()
    print('Data Validation: {0} cells updated.'.format(len(response.get('replies'))))


def main_schedule_build(services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict):
    service = auth_service()
    response = create_blank_sheet(service)
    spreadsheet_id = response['spreadsheetId']

    # CONSTANTS
    data_start_row = 3
    data_end_row = data_start_row + len(doctors)
    data_start_col = 4
    data_end_col = data_start_col + len(blocks_list)

    build_core_schedule(service, spreadsheet_id, doctors, blocks_list, service_constraint_dict)
    # append_constraints(service, spreadsheet_id, doctors, blocks, rotation_constraints)
    add_conditional_format(service, spreadsheet_id, doctors, blocks_list, service_constraint_dict)
    add_doctor_row_constraints(service, spreadsheet_id, doctors, doctor_constraint_dict, services)
    add_data_validation(service, spreadsheet_id, services,
                        start_row=data_start_row, end_row=data_end_row,
                        start_col=data_start_col, end_col=data_end_col)



if __name__ == '__main__':
    ## CONSTANTS #################################
    # 1.1 Data Entry
    data_entry_sheet = '1.1 Data Entry'
    services_list_range = InputRange(data_entry_sheet, 6, 2, 32, 2)
    training_list_range = InputRange(data_entry_sheet, 6, 4, 10, 4)

    # 1.2 Doctors
    doctors_sheet = '1.2 Doctors'
    doctors_table_range = InputRange(doctors_sheet, 6, 2, 35, 4)

    # 1.3 Dates
    dates_sheet = '1.3 Dates'
    block_table_range = InputRange(dates_sheet, 6, 2, 9, 5)

    # 2.1 Coverage Reqs
    coverage_sheet = '2.1 Coverage Reqs'
    coverage_table_range = InputRange(coverage_sheet, 6, 2, 31, 5)

    # 2.2 Personal Reqs
    personal_sheet = '2.2 Personal Reqs'
    personal_table_range = InputRange(personal_sheet, 6, 2, 31, 5)

    ranges = {'services': services_list_range,
              'trainings': training_list_range,
              'doctors': doctors_table_range,
              'blocks': block_table_range,
              'coverage': coverage_table_range,
              'personal': personal_table_range}

    ##############################################
    from googlesheets.read_input import parse_input_data

    print(ranges['services'].to_range_string())
    test_id = '1EOkBaSd_99jGVGIoPHYNlCLfdH17AHpiqDElb1kAQw4'
    services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict = parse_input_data(
        test_id, ranges)
    blocks_list = blocks_list[0][0]
    print(services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict)

    # Output Dimensions
    data_start_row = 3
    data_end_row = data_start_row + len(doctors)
    data_start_col = 4
    data_end_col = data_start_col + len(blocks_list)
    main_schedule_build(services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict)

    # TODO: fix going over the Z (AA, AB, etc column -- need to edit the number to column letter function)
    # TODO: fix the rotations with no role not summing properly
    # TODO: add to the existing spreadsheet instead of making a new one