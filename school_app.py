from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import get_session
from models import Course, Department, Student, StudentProfile, Teacher
from schemas import StudentCreate, StudentOut, StudentProfileOut, StudentUpdate

app = FastAPI(title="School ORM App")


@app.get("/students", response_model=list[StudentOut])
def list_students(
    session: Session = Depends(get_session),
    status_filter: str | None = Query(default=None),
):
    stmt = select(Student).options(selectinload(Student.department), selectinload(Student.profile))
    if status_filter:
        stmt = stmt.where(Student.status == status_filter)
    stmt = stmt.order_by(Student.full_name)
    return session.scalars(stmt).all()


@app.get("/students/{student_id}", response_model=StudentOut)
def student_detail(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    department = session.get(Department, student.department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    record = Student(
        full_name=student.full_name,
        email=student.email,
        birth_date=student.birth_date,
        department_id=student.department_id,
        status=student.status,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@app.patch("/students/{student_id}", response_model=StudentOut)
def update_student(student_id: int, payload: StudentUpdate, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    updates = payload.model_dump(exclude_unset=True)
    if "department_id" in updates:
        department = session.get(Department, updates["department_id"])
        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

    for key, value in updates.items():
        setattr(student, key, value)

    session.commit()
    session.refresh(student)
    return student


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, session: Session = Depends(get_session)):
    student = session.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()
    return None


@app.get("/api/students")
def api_students(session: Session = Depends(get_session)):
    students = session.scalars(select(Student).order_by(Student.full_name)).all()
    return [{
        "id": s.id,
        "full_name": s.full_name,
        "email": s.email,
        "birth_date": s.birth_date.isoformat(),
        "department_id": s.department_id,
        "status": s.status,
    } for s in students]


@app.get("/departments")
def list_departments(session: Session = Depends(get_session)):
    departments = session.scalars(select(Department).order_by(Department.name)).all()
    rows = []
    for dept in departments:
        rows.append({
            "id": dept.id,
            "name": dept.name,
            "parent": dept.parent.name if dept.parent else None,
            "level_name": dept.level_name,
        })
    return rows


@app.get("/courses/{course_id}")
def course_detail(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return {
        "id": course.id,
        "title": course.title,
        "teacher": course.teacher.full_name,
        "credits": course.credits,
        "schedule": course.schedule,
        "students": [student.full_name for student in course.students],
    }


@app.get("/tree")
def department_tree(session: Session = Depends(get_session)):
    roots = session.scalars(select(Department).where(Department.parent_id.is_(None)).order_by(Department.name)).all()
    lines: list[str] = []

    def walk(node: Department, depth: int = 0):
        lines.append("  " * depth + node.name)
        for child in sorted(node.children, key=lambda item: item.name):
            walk(child, depth + 1)

    for root in roots:
        walk(root)

    return HTMLResponse("<pre>" + "\n".join(lines) + "</pre>")


@app.get("/")
def root() -> dict[str, str]:
    return {"catalogue": "School Catalogue"}
