from datetime import date, time
from uuid import UUID
from sqlalchemy import BigInteger, Date, ForeignKey, Time, Uuid, text
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.base import Base

# from database import Teacher, LessonDay
from . import teacher, lesson_day


class LessonWeek(Base):
    __tablename__ = 'lessons_week'

    week_id: Mapped[UUID] = mapped_column(Uuid,
                                          primary_key=True,
                                          server_default=text("gen_random_uuid()"))

    week_date: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
        primary_key=True
    )

    teacher_id: Mapped[int] = mapped_column(BigInteger,
                                            ForeignKey('teachers.teacher_id', ondelete='cascade'),
                                            primary_key=True,
                                            )

    # student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('students.student_id'),
    #                                        )

    work_start: Mapped[time] = mapped_column(Time)
    work_end: Mapped[time] = mapped_column(Time)

    teacher: Mapped["teacher.Teacher"] = relationship(back_populates='weeks',
                                                      )
    lessons: Mapped[list["lesson_day.LessonDay"]] = relationship(back_populates='week',
                                                                 cascade='delete')
