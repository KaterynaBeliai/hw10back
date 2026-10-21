# School management domain

This project models a small school management system. The system tracks academic units, teachers, courses, and student records. The main table is `students`, because it is the central entity of the school domain: each student belongs to a department, can attend many courses, has a department hierarchy path, and may optionally have additional contact information stored separately.

Tables:
- departments — school units arranged in a hierarchy with parent and child departments.
- teachers — staff members who teach courses.
- courses — classes taught by teachers and taken by students.
- students — the main table of the school domain; each student belongs to one department.
- student_profiles — one-to-one extra data for selected students only.
- student_courses — the junction table linking students to courses in a many-to-many relationship.

## Relationship map

| Relationship type | Tables involved | Column implementing it | Route where it is visible | SQL used | Why the domain needs it |
| --- | --- | --- | --- | --- | --- |
| One-to-many | students -> departments | students.department_id | /student/{id}/en and /department/{id}/en | SELECT s.id, s.full_name, d.name FROM students s JOIN departments d ON d.id = s.department_id | Every student belongs to exactly one department, but one department contains many students. |
| One-to-many | courses -> teachers | courses.teacher_id | /course/{id}/en | SELECT c.id, c.title, t.full_name FROM courses c JOIN teachers t ON t.id = c.teacher_id | One teacher can teach many courses, but each course has a single teacher. |
| Many-to-many | students <-> courses | student_courses.student_id + student_courses.course_id | /student/{id}/en and /course/{id}/en | SELECT c.title FROM student_courses sc JOIN courses c ON c.id = sc.course_id WHERE sc.student_id = %s | A student can enroll in many courses, and one course can be taken by many students. |
| One-to-one | students <-> student_profiles | student_profiles.student_id | /student/{id}/en | SELECT sp.phone, sp.emergency_contact FROM student_profiles sp WHERE sp.student_id = %s | Some extra details are optional and are stored separately because not every student has them. |
| Self-reference | departments -> departments | departments.parent_id | /departments/en | WITH RECURSIVE tree AS (...) SELECT ... FROM departments | The school is structured as a hierarchy: school > primary > grade 1, so each unit may have a parent department. |

## Why the one-to-one table is separate

The extra data is not simply more columns on the students table because only a subset of students has this information. If every student had phone and emergency contact fields, the table would be wider and less efficient, and optional values would need to be filled with nulls or placeholders. Separating it into `student_profiles` keeps the main table cleaner, preserves the rule that only a few rows have extra information, and makes it possible to enforce a strict one-to-one relationship without wasting space on every student.

In a different situation, if the project later required every student to have a phone number and emergency contact immediately, it would make sense to move these fields back into the `students` table as normal columns.

## ER diagram

```text
teachers
  1 ────< * courses
               │
               │
               *
students ────< student_courses >───── courses
   │
   │ 1 ────── 1
   │
   └─── student_profiles

departments
   1 ────< * departments (parent_id self-reference)
   │
   └─── * students
```

The diagram shows the required four relationship patterns:
- one-to-many from teachers to courses,
- one-to-many from departments to students,
- many-to-many through `student_courses`,
- one-to-one through `student_profiles`,
- and a self-referencing hierarchy on `departments.parent_id`.
