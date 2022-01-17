from googlesheets.block_schedule import auth_service
from googlesheets.helpers import *
from googlesheets.input_range import InputRange
from googlesheets.constraint import RotationReq

"""
This file determines what ranges to look at to parse input.
The correct InputRange object is of the format:
InputRange(start_row, start_col, end_row, end_col)
The input parser file will read from here to determine 
where from the sheet to grab data.
"""
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

from googleapiclient import discovery


def read_values(service, spreadsheet_id, input_range):
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=input_range)
    response = request.execute()
    values = response.get('values', [])
    return values


def parse_constraint_table(coverage_raw):
    prelim_constraint_dict = {}
    for service, roles_str, constraint_str, value_str in coverage_raw:
        roles_list = [x.strip() for x in roles_str.split(',')]
        if roles_list == ['ALL']: roles_list = []
        constraint = get_constraint_from_str(constraint_str)
        value = int(value_str)
        if service in prelim_constraint_dict:
            prelim_constraint_dict[service].append((roles_list, constraint, value))
        else:
            prelim_constraint_dict[service] = [(roles_list, constraint, value)]
    constraint_dict = {}
    for service, req_info in prelim_constraint_dict.items():
        req_list = []
        for roles_list, constraint, value in req_info:
            req = RotationReq(constraint, value, roles_list)
            req_list.append(req)
        constraint_dict[service] = req_list
    return constraint_dict


def parse_input_data(spreadsheet_id, ranges):
    service = auth_service()

    # SERVICES == ROTATIONS
    services_raw = read_values(service, spreadsheet_id, ranges['services'].to_range_string())
    services = flatten_list(services_raw)

    trainings_raw = read_values(service, spreadsheet_id, ranges['trainings'].to_range_string())
    trainings = flatten_list(trainings_raw)

    doctors_raw = read_values(service, spreadsheet_id, ranges['doctors'].to_range_string())
    doctors = {doctor[0] + ' ' + doctor[1]: doctor[2] for doctor in doctors_raw}

    blocks_raw = read_values(service, spreadsheet_id, ranges['blocks'].to_range_string())
    blocks_list = [] # will become [(list of block segments, role), ...]
    for block_setup in blocks_raw:
        block_duration_weeks, start, end = block_setup[0:3]
        block_role = block_setup[3] if len(block_setup) == 4 else None
        segmented_dates_list = blocks_builder(
            parse_datetime_from_string(start),
            parse_datetime_from_string(end),
            int(block_duration_weeks) * 7)
        blocks_list.append((segmented_dates_list, block_role))

    service_coverage_raw_unfiltered = read_values(service, spreadsheet_id, ranges['coverage'].to_range_string())
    service_coverage_raw = [row for row in service_coverage_raw_unfiltered if len(row) == 4]
    service_constraint_dict = parse_constraint_table(service_coverage_raw)

    doctor_coverage_raw_unfiltered = read_values(service, spreadsheet_id, ranges['personal'].to_range_string())
    doctor_coverage_raw = [[row[1], row[0], row[2], row[3]] for row in doctor_coverage_raw_unfiltered if len(row) == 4]
    print(doctor_coverage_raw)
    doctor_constraint_dict = parse_constraint_table(doctor_coverage_raw)

    print(services, trainings, doctors, doctor_constraint_dict)
    return services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict






if __name__ == '__main__':
    print(ranges['services'].to_range_string())
    test_id = '1EOkBaSd_99jGVGIoPHYNlCLfdH17AHpiqDElb1kAQw4'
    services, trainings, doctors, blocks_list, service_constraint_dict, doctor_constraint_dict = parse_input_data(test_id, ranges)





