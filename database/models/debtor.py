from datetime import time
from uuid import UUID

from sqlalchemy import Uuid, BigInteger, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Debtor(Base):
    __tablename__ = 'debtors'

    debtor_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('teachers.teacher_id', ondelete='cascade'))
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('students.student_id', ondelete='cascade'))
    lesson_on: Mapped[time] = mapped_column(Time)
    lesson_off: Mapped[time] = mapped_column(Time)
