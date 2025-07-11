from .models.debtor import Debtor
from .models.teacher import Teacher
from .models.student import Student
from .models.lesson_week import LessonWeek
from .models.lesson_day import LessonDay
from .models.access_student import AccessStudent
from .models.access_teacher import AccessTeacher
from .models.penalty import Penalty

__all__ = [
    "Teacher",
    "Student",
    "LessonWeek",
    "LessonDay",
    "Penalty",
    "AccessStudent",
    "AccessTeacher",
    "Debtor"
]