from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

student_courses = Table(
    "student_courses",
    Base.metadata,
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="SET NULL"), index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    level_name: Mapped[str] = mapped_column(String(50), nullable=False)

    parent: Mapped[Department | None] = relationship(
        back_populates="children",
        remote_side="Department.id",
    )
    children: Mapped[list[Department]] = relationship(
        back_populates="parent",
    )
    students: Mapped[list["Student"]] = relationship(back_populates="department")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    office: Mapped[str] = mapped_column(String(200), nullable=False)

    courses: Mapped[list["Course"]] = relationship(back_populates="teacher")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="RESTRICT"), index=True, nullable=False)
    credits: Mapped[int] = mapped_column(nullable=False)
    schedule: Mapped[str] = mapped_column(String(200), nullable=False)

    teacher: Mapped[Teacher] = relationship(back_populates="courses")
    students: Mapped[list["Student"]] = relationship(secondary=student_courses, back_populates="courses")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    birth_date: Mapped[date] = mapped_column(nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    department: Mapped[Department] = relationship(back_populates="students")
    profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )
    courses: Mapped[list[Course]] = relationship(secondary=student_courses, back_populates="students")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    emergency_contact: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    student: Mapped[Student] = relationship(back_populates="profile")
