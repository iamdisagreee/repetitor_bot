from datetime import datetime, time

from sqlalchemy import BigInteger, String, DateTime, func, Time, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from bot.database.base import Base
from . import student, lesson_week


class Teacher(Base):
    __tablename__ = 'teachers'

    teacher_id: Mapped[int] = mapped_column(primary_key=True, type_=BigInteger)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    bank: Mapped[str] = mapped_column(String)
    penalty: Mapped[int] = mapped_column(Integer)
    until_hour_notification: Mapped[int] = mapped_column(Integer,
                                                         nullable=True)
    until_minute_notification: Mapped[int] = mapped_column(Integer,
                                                           nullable=True)
    daily_schedule_mailing_time: Mapped[time] = mapped_column(Time,
                                                              nullable=True)
    daily_report_mailing_time: Mapped[time] = mapped_column(Time,
                                                            nullable=True)
    daily_confirmation_notification: Mapped[int] = mapped_column(Integer,
                                                                 nullable=True)
    days_cancellation_notification: Mapped[int] = mapped_column(Integer,
                                                                nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    students: Mapped[list["student.Student"]] = relationship(back_populates='teacher',
                                                             cascade='delete')
    weeks: Mapped["lesson_week.LessonWeek"] = relationship(back_populates='teacher',
                                                                 cascade='delete')
