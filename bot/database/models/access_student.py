from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import expression
from sqlalchemy.sql.functions import func

from bot.database.base import Base

from . import student


class AccessStudent(Base):
    __tablename__ = 'access_students'

    student_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    status: Mapped[bool] = mapped_column(Boolean,
                                         server_default=expression.true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now())

    student: Mapped["student.Student"] = relationship(back_populates='access',
                                                      cascade='delete')
