from datetime import date, time
from uuid import UUID

from sqlalchemy import BigInteger, Date, Time, ForeignKey, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.base import Base
from . import student


class Penalty(Base):
    __tablename__ = 'penalties'

    penalty_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True,
                                             server_default=text("gen_random_uuid()"))

    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('students.student_id',
                                                                   ondelete='cascade'))
    week_date: Mapped[date] = mapped_column(Date)
    lesson_on: Mapped[time] = mapped_column(Time)
    lesson_off: Mapped[time] = mapped_column(Time)

    student: Mapped["student.Student"] = relationship('Student', back_populates='penalties')