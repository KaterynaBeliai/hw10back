from __future__ import annotations

from datetime import date

from database import SessionLocal
from models import Course, Department, Student, StudentProfile, Teacher


def seed(session):
    school = Department(
        name="School",
        parent_id=None,
        description="Main school organization",
        level_name="school",
    )
    primary = Department(
        name="Primary School",
        parent_id=None,
        description="Lower grades",
        level_name="group",
    )
    middle = Department(
        name="Middle School",
        parent_id=None,
        description="Middle grades",
        level_name="group",
    )
    high = Department(
        name="High School",
        parent_id=None,
        description="Upper grades",
        level_name="group",
    )
    grade_1 = Department(
        name="Grade 1",
        parent_id=None,
        description="First-year students",
        level_name="class",
    )
    grade_5 = Department(
        name="Grade 5",
        parent_id=None,
        description="Fifth-year students",
        level_name="class",
    )
    grade_9 = Department(
        name="Grade 9",
        parent_id=None,
        description="Ninth-year students",
        level_name="class",
    )
    grade_11 = Department(
        name="Grade 11",
        parent_id=None,
        description="Eleventh-year students",
        level_name="class",
    )

    primary.parent = school
    middle.parent = school
    high.parent = school
    grade_1.parent = primary
    grade_5.parent = middle
    grade_9.parent = high
    grade_11.parent = high

    nora = Teacher(full_name="Nora Smith", subject="Mathematics", email="nora.smith@school.edu", office="A101")
    leo = Teacher(full_name="Leo Brown", subject="Biology", email="leo.brown@school.edu", office="B204")
    ava = Teacher(full_name="Ava Johnson", subject="History", email="ava.johnson@school.edu", office="C110")
    milo = Teacher(full_name="Milo Garcia", subject="Literature", email="milo.garcia@school.edu", office="D305")

    algebra = Course(title="Algebra I", teacher=nora, credits=3, schedule="Mon/Wed 09:00")
    biology = Course(title="Biology Basics", teacher=leo, credits=4, schedule="Tue/Thu 10:30")
    history = Course(title="World History", teacher=ava, credits=3, schedule="Mon/Fri 11:00")
    literature = Course(title="English Literature", teacher=milo, credits=3, schedule="Wed/Fri 13:00")
    geometry = Course(title="Geometry", teacher=nora, credits=3, schedule="Tue/Thu 09:00")
    chemistry = Course(title="Chemistry", teacher=leo, credits=4, schedule="Mon/Wed 14:00")

    emma = Student(
        full_name="Emma Wilson",
        email="emma.wilson@school.edu",
        birth_date=date(2010, 5, 14),
        status="active",
        department=grade_1,
        courses=[algebra, biology, literature],
    )
    liam = Student(
        full_name="Liam Martin",
        email="liam.martin@school.edu",
        birth_date=date(2010, 2, 11),
        status="active",
        department=grade_1,
        courses=[algebra, history],
    )
    olivia = Student(
        full_name="Olivia Davis",
        email="olivia.davis@school.edu",
        birth_date=date(2010, 4, 18),
        status="active",
        department=grade_1,
        courses=[biology, literature],
    )
    noah = Student(
        full_name="Noah Thompson",
        email="noah.thompson@school.edu",
        birth_date=date(2009, 8, 9),
        status="active",
        department=grade_5,
        courses=[algebra, geometry],
    )
    sophia = Student(
        full_name="Sophia Moore",
        email="sophia.moore@school.edu",
        birth_date=date(2009, 7, 7),
        status="active",
        department=grade_5,
        courses=[biology, chemistry],
    )
    mason = Student(
        full_name="Mason Garcia",
        email="mason.garcia@school.edu",
        birth_date=date(2009, 12, 1),
        status="active",
        department=grade_5,
        courses=[history, literature],
    )
    isabella = Student(
        full_name="Isabella Lee",
        email="isabella.lee@school.edu",
        birth_date=date(2008, 3, 21),
        status="active",
        department=grade_9,
        courses=[algebra, literature, geometry],
    )
    jacob = Student(
        full_name="Jacob Clark",
        email="jacob.clark@school.edu",
        birth_date=date(2008, 11, 30),
        status="active",
        department=grade_9,
        courses=[biology, history, chemistry],
    )
    ava_r = Student(
        full_name="Ava Rodriguez",
        email="ava.rodriguez@school.edu",
        birth_date=date(2008, 6, 17),
        status="active",
        department=grade_9,
        courses=[algebra, literature],
    )
    lucas = Student(
        full_name="Lucas Walker",
        email="lucas.walker@school.edu",
        birth_date=date(2007, 9, 6),
        status="active",
        department=grade_11,
        courses=[geometry, chemistry],
    )
    mia = Student(
        full_name="Mia Hall",
        email="mia.hall@school.edu",
        birth_date=date(2007, 1, 26),
        status="on_leave",
        department=grade_11,
        courses=[biology, history],
    )
    james = Student(
        full_name="James Young",
        email="james.young@school.edu",
        birth_date=date(2007, 4, 12),
        status="graduated",
        department=grade_11,
        courses=[algebra, literature],
    )

    session.add_all([school, primary, middle, high, grade_1, grade_5, grade_9, grade_11, nora, leo, ava, milo])
    session.add_all([algebra, biology, history, literature, geometry, chemistry])
    session.add_all([
        emma, liam, olivia, noah, sophia, mason, isabella, jacob, ava_r, lucas, mia, james,
    ])
    session.add_all([
        StudentProfile(student=emma, phone="+1-555-0101", emergency_contact="Anna Wilson - mother", notes="Enjoys mathematics club."),
        StudentProfile(student=noah, phone="+1-555-0104", emergency_contact="Daniel Martin - father", notes="Needs extra reading support."),
        StudentProfile(student=jacob, phone="+1-555-0108", emergency_contact="Susan Clark - mother", notes="Prefers project-based learning."),
    ])

    session.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
