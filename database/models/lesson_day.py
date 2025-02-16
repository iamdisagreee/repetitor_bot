from datetime import datetime, date, time

from sqlalchemy import BigInteger, Date, func, Integer, ForeignKey, Time, text, Boolean, ForeignKeyConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import expression

from database.base import Base
# from database import LessonWeek, Student
from . import lesson_week, student


class LessonDay(Base):
    __tablename__ = 'lessons_day'

    lesson_id: Mapped[int] = mapped_column(Integer, primary_key=True,
                                           autoincrement=True)

    # week_id: Mapped[int] = mapped_column(
    #     BigInteger,
    #     ForeignKey('lessons_week.week_id'),
    # )

    week_id: Mapped[int] = mapped_column(Integer)

    week_date: Mapped[date] = mapped_column(
        Date,
        #ForeignKey('lessons_week.week_date'),
    )

    teacher_id: Mapped[int] = mapped_column(
        BigInteger,
        #ForeignKey('teachers.teacher_id'),
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

    status: Mapped[bool] = mapped_column(Boolean,
                                         nullable=True,
                                         server_default=expression.false(),
                                        )

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
