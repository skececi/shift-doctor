from datetime import timedelta, datetime

DEFAULTS = {
    'MONTHLY': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    
}

# taking input from the format '06/01/20'
# TODO: use this --> dateutil.parser to auto parse
def parse_datetime_from_string(date_string):
    return datetime.strptime(date_string, '%m/%d/%y')

def blocks_builder(start_date, end_date, block_length_days):
    print('blocks builder: ', start_date, end_date, block_length_days)
    l = generate_blocks(start_date, end_date, int(block_length_days))
    l_str = [block_tup_to_string(block_tup) for block_tup in l]
    return l_str


def generate_blocks(start_date, end_date, block_length_days):
    # will be in the form: [(start1, end1), (start2, end2), ...]
    blocks_list = []
    curr_date = start_date
    while curr_date < end_date:
        end_of_block = curr_date + timedelta(days=block_length_days - 1)  # This -1 needs to be clarified!
        curr_tup = (curr_date, end_of_block)
        blocks_list.append(curr_tup)
        curr_date = end_of_block + timedelta(days=1)
    return blocks_list


def block_tup_to_string(block_tup):
    return block_tup[0].strftime('%b %d') + '-' + block_tup[1].strftime('%b %d')


def letter_from_num(num):
    return chr(ord('@') + num)

def flatten_list(two_dim_list):
    return [item for row in two_dim_list for item in row]

def get_constraint_from_str(constraint_str):
    from googlesheets.constraint import Constraint
    if constraint_str == 'MIN':
        return Constraint.MIN
    elif constraint_str == 'EXACTLY':
        return Constraint.EXACTLY
    elif constraint_str == 'MAX':
        return Constraint.MAX
    else:
        raise NameError("Incorrect constraint, must be one of MIN, EXACTLY, MAX. Input was: ", constraint_str)


