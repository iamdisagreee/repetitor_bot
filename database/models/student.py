from datetime import datetime

from sqlalchemy import BigInteger, func, Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

from database.base import Base
# from database import Teacher, LessonDay
from . import teacher, lesson_day


class Student(Base):
    __tablename__ = 'students'

    student_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    surname: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    place_study: Mapped[str] = mapped_column(String(20))
    class_learning: Mapped[int] = mapped_column(Integer)
    course_learning: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(20))
    teacher_id: Mapped[int] = mapped_column(BigInteger,
                                            ForeignKey('teachers.teacher_id',
                                                       ondelete='cascade'))
    price: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    teacher: Mapped["teacher.Teacher"] = relationship(back_populates='students',
                                                      )
    lessons: Mapped[list["lesson_day.LessonDay"]] = relationship(back_populates='student',
                                                                 )
