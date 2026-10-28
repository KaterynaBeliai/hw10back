DROP TABLE IF EXISTS student_courses;
DROP TABLE IF EXISTS student_profiles;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id serial PRIMARY KEY,
    name text NOT NULL UNIQUE,
    parent_id integer REFERENCES departments(id) ON DELETE SET NULL,
    description text NOT NULL,
    level_name text NOT NULL,
    CHECK (parent_id <> id)
);
CREATE INDEX idx_departments_parent_id ON departments(parent_id);

CREATE TABLE teachers (
    id serial PRIMARY KEY,
    full_name text NOT NULL UNIQUE,
    subject text NOT NULL,
    email text NOT NULL UNIQUE,
    office text NOT NULL
);

CREATE TABLE courses (
    id serial PRIMARY KEY,
    title text NOT NULL UNIQUE,
    teacher_id integer NOT NULL REFERENCES teachers(id) ON DELETE RESTRICT,
    credits integer NOT NULL CHECK (credits > 0),
    schedule text NOT NULL
);
CREATE INDEX idx_courses_teacher_id ON courses(teacher_id);


CREATE TABLE students (
    id serial PRIMARY KEY,
    full_name text NOT NULL,
    email text NOT NULL UNIQUE,
    birth_date date NOT NULL,
    department_id integer NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    status text NOT NULL CHECK (status IN ('active', 'on_leave', 'graduated'))
);
CREATE INDEX idx_students_department_id ON students(department_id);

CREATE TABLE student_profiles (
    student_id integer PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    phone text NOT NULL UNIQUE,
    emergency_contact text NOT NULL,
    notes text
);

CREATE TABLE student_courses (
    student_id integer NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id integer NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, course_id)
);
CREATE INDEX idx_student_courses_course_id ON student_courses(course_id);

INSERT INTO departments (name, parent_id, description, level_name) VALUES
    ('School', NULL, 'Main school organization', 'school'),
    ('Primary School', 1, 'Lower grades', 'group'),
    ('Middle School', 1, 'Middle grades', 'group'),
    ('High School', 1, 'Upper grades', 'group'),
    ('Grade 1', 2, 'First-year students', 'class'),
    ('Grade 5', 3, 'Fifth-year students', 'class'),
    ('Grade 9', 4, 'Ninth-year students', 'class'),
    ('Grade 11', 4, 'Eleventh-year students', 'class');

INSERT INTO teachers (full_name, subject, email, office) VALUES
    ('Nora Smith', 'Mathematics', 'nora.smith@school.edu', 'A101'),
    ('Leo Brown', 'Biology', 'leo.brown@school.edu', 'B204'),
    ('Ava Johnson', 'History', 'ava.johnson@school.edu', 'C110'),
    ('Milo Garcia', 'Literature', 'milo.garcia@school.edu', 'D305');

INSERT INTO courses (title, teacher_id, credits, schedule) VALUES
    ('Algebra I', 1, 3, 'Mon/Wed 09:00'),
    ('Biology Basics', 2, 4, 'Tue/Thu 10:30'),
    ('World History', 3, 3, 'Mon/Fri 11:00'),
    ('English Literature', 4, 3, 'Wed/Fri 13:00'),
    ('Geometry', 1, 3, 'Tue/Thu 09:00'),
    ('Chemistry', 2, 4, 'Mon/Wed 14:00');

INSERT INTO students (full_name, email, birth_date, department_id, status) VALUES
    ('Emma Wilson', 'emma.wilson@school.edu', '2010-05-14', 5, 'active'),
    ('Liam Martin', 'liam.martin@school.edu', '2010-02-11', 5, 'active'),
    ('Olivia Davis', 'olivia.davis@school.edu', '2010-04-18', 5, 'active'),
    ('Noah Thompson', 'noah.thompson@school.edu', '2009-08-09', 6, 'active'),
    ('Sophia Moore', 'sophia.moore@school.edu', '2009-07-07', 6, 'active'),
    ('Mason Garcia', 'mason.garcia@school.edu', '2009-12-01', 6, 'active'),
    ('Isabella Lee', 'isabella.lee@school.edu', '2008-03-21', 7, 'active'),
    ('Jacob Clark', 'jacob.clark@school.edu', '2008-11-30', 7, 'active'),
    ('Ava Rodriguez', 'ava.rodriguez@school.edu', '2008-06-17', 7, 'active'),
    ('Lucas Walker', 'lucas.walker@school.edu', '2007-09-06', 8, 'active'),
    ('Mia Hall', 'mia.hall@school.edu', '2007-01-26', 8, 'on_leave'),
    ('James Young', 'james.young@school.edu', '2007-04-12', 8, 'graduated');

INSERT INTO student_profiles (student_id, phone, emergency_contact, notes) VALUES
    (1, '+1-555-0101', 'Anna Wilson - mother', 'Enjoys mathematics club.'),
    (4, '+1-555-0104', 'Daniel Martin - father', 'Needs extra reading support.'),
    (8, '+1-555-0108', 'Susan Clark - mother', 'Prefers project-based learning.');

INSERT INTO student_courses (student_id, course_id) VALUES
    (1, 1), (1, 2), (1, 4),
    (2, 1), (2, 3),
    (3, 2), (3, 4),
    (4, 1), (4, 5),
    (5, 2), (5, 6),
    (6, 3), (6, 4),
    (7, 1), (7, 4), (7, 5),
    (8, 2), (8, 3), (8, 6),
    (9, 1), (9, 4),
    (10, 5), (10, 6),
    (11, 2), (11, 3),
    (12, 1), (12, 4);
