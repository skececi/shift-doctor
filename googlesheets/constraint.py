from enum import Enum


class Constraint(Enum):
    MIN = -1
    EXACTLY = 0
    MAX = 1


class RotationReq:
    def __init__(self, constraint, value, roles=[]):
        self.constraint = constraint
        self.value = value
        self.roles = roles if roles else []

    def __str__(self):
        return self.constraint.name + ' ' + str(self.value)

    def str_roles(self):
        s = ''
        for role in self.roles:
            s += role
            s += ', '
        return s[:-2]

    def roles_to_formula_array(self):
        s = '{"'
        for role in self.roles:
            s += role
            s += '", "'
        s = s[:-3] + '}'
        return s
    
    def full_info_str(self):
        return self.constraint.name + ' ' + str(self.value) + ' (' + self.str_roles() + ')'


