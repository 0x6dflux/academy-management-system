from account.permissions.is_education_officer import IsEducationOfficerOrAdmin
from account.permissions.is_finance_officer import IsFinanceOfficerOrAdmin
from account.permissions.is_role_admin import IsRoleAdmin
from account.permissions.is_teacher import IsTeacherOrAdmin

__all__ = [
    "IsEducationOfficerOrAdmin",
    "IsFinanceOfficerOrAdmin",
    "IsRoleAdmin",
    "IsTeacherOrAdmin",
]
