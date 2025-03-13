from datetime import time, date
from uuid import UUID

from sqlalchemy import Uuid, BigInteger, ForeignKey, Time, text, Date, func, Integer
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Debtor(Base):
    __tablename__ = 'debtors'

    debtor_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, server_default=text("gen_random_uuid()"))
    teacher_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('teachers.teacher_id', ondelete='cascade'))
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('students.student_id', ondelete='cascade'))
    week_date: Mapped[date] = mapped_column(Date, server_default=func.now())
    lesson_on: Mapped[time] = mapped_column(Time)
    lesson_off: Mapped[time] = mapped_column(Time)
    amount_money: Mapped[int] = mapped_column(Integer)
