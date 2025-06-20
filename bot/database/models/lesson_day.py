from datetime import date, time
from uuid import UUID

from sqlalchemy import BigInteger, Date, ForeignKey, Time, text, Boolean, ForeignKeyConstraint, Uuid, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import expression

from bot.database.base import Base
# from database import LessonWeek, Student
from . import lesson_week, student


class LessonDay(Base):
    __tablename__ = 'lessons_day'

    lesson_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True,
                                            server_default=text("gen_random_uuid()"))

    week_id: Mapped[UUID] = mapped_column(Uuid)

    week_date: Mapped[date] = mapped_column(
        Date,
    )

    teacher_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('students.student_id', ondelete='cascade'),
    )

    lesson_start: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    lesson_finished: Mapped[time] = mapped_column(
        Time,
        nullable=False
    )

    is_formed: Mapped[int] = mapped_column(Boolean,server_default=expression.false())

    status: Mapped[bool] = mapped_column(Boolean,
                                         nullable=True,
                                         server_default=expression.false(),
                                         )

    student_mailing_status: Mapped[int] = mapped_column(Integer,
                                                         server_default='0')

    teacher_mailing_status: Mapped[int] = mapped_column(Integer,
                                                         server_default='0')

    __table_args__ = (ForeignKeyConstraint(['week_id', 'week_date', 'teacher_id'],
                                           [lesson_week.LessonWeek.week_id,
                                            lesson_week.LessonWeek.week_date,
                                            lesson_week.LessonWeek.teacher_id],
                                           ondelete='cascade'),
                      {})

    week: Mapped["lesson_week.LessonWeek"] = relationship(back_populates='lessons',
                                                          )
    student: Mapped["student.Student"] = relationship(back_populates='lessons',
                                                      )
