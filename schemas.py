from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class StudentProfileOut(BaseModel):
    student_id: int
    phone: str
    emergency_contact: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentOut(BaseModel):
    id: int
    full_name: str
    email: str
    birth_date: date
    department_id: int
    status: str
    profile: StudentProfileOut | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=1, max_length=200)
    birth_date: date
    department_id: int
    status: str = Field(..., pattern=r"^(active|on_leave|graduated)$")


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, min_length=1, max_length=200)
    birth_date: date | None = None
    department_id: int | None = None
    status: str | None = Field(default=None, pattern=r"^(active|on_leave|graduated)$")
