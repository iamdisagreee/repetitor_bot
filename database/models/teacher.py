from datetime import date, datetime

from sqlalchemy import BigInteger, String, DateTime, func, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.base import Base
# from database import Student, LessonWeek
from . import student, lesson_week


class Teacher(Base):
    __tablename__ = 'teachers'

    teacher_id: Mapped[int] = mapped_column(primary_key=True, type_=BigInteger)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    students: Mapped[list["student.Student"]] = relationship(back_populates='teacher',
                                                             cascade='delete')
    weeks: Mapped["lesson_week.LessonWeek"] = relationship(back_populates='teacher',
                                                                 cascade='delete')
