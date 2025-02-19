from datetime import date, time
from uuid import UUID

from sqlalchemy import BigInteger, Integer, Date, Time, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from . import student


class Penalty(Base):

    __tablename__ = 'penalties'
    penalty_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('students.student_id'))
    week_date: Mapped[date] = mapped_column(Date())
    lesson_on: Mapped[time] = mapped_column(Time())
    lesson_off: Mapped[time] = mapped_column(Time())

    student: Mapped["student.Student"] = relationship(back_populates='penalties')
