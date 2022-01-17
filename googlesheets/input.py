from .helpers import blocks_builder, DEFAULTS
from datetime import date


"""
*doctors
A list of doctor_name : training pairs
example: 
doctors = {'Sam K': 'PGY1',
           'Cansu': 'PGY2',
           }
"""
doctors = {}


"""
*blocks
use the generate_blocks function to seqment into dates
use Datetime object for start and end date
blocks_builder(start_date, end_date, block_length_days)
e.g. 
blocks_builder(date(2020, 6, 1), date(2021, 5, 31), 14)
above would generate blocks of 14 days starting June 1, 2020 and ending May 31, 2021
"""
blocks = blocks_builder(date(2020, 6, 1), date(2021, 5, 31), 14)
# blocks = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
# blocks = DEFAULTS['MONTHLY']

"""
*rotations
list of rotations
"""
rotations = ['ICU', 'Clinic']


"""
*rotation_constraints
a list of rotations with the corresponding constraints (coverage reqs)
example: 
{'ICU': [RotationReq(Constraint.EXACTLY, 1, ['PGY1', 'PGY2']), ],
 'Clinic': [RotationReq(Constraint.MIN, 2, ['PGY1']),
            RotationReq(Constraint.MAX, 5, ['PGY2'])],
'Surgery': [RotationReq(Constraint.EXACTLY, 1, ['PGY2'])],
'Vacation': [],
}
notes: 
--all constraints in the form of a list [...]
--for no constraints, use an empty list []
--for multiple constraints, use a list seperated by commas 
e.g. [RotationReq(Constraint.MIN, 2, ['PGY1']), RotationReq(Constraint.MAX, 5, ['PGY2'])]
-- each individual constraint takes the following form:
RotationReq(Constraint.<MIN/MAX/EXACTLY>, <value>, [<list of roles>])
"""
rotation_constraints = {}


"""
*doctor_constraints
to be summed across the rows (for each individual doctor)
same format as above (including the RotationReq signature)
"""
doctor_constraints = {}
