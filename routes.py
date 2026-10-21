import html
from urllib.parse import parse_qsl

import db
from auth import login_required
from http_parser import parse_query_string
from response import HTMLResponse, RedirectResponse, JSONResponse, Response
from sessions import sessions, create_session
from users import check_password, USERS
from tokens import make_token, verify_token

app = None


def _escape(value):
    return html.escape(str(value), quote=False)


def _student_id_from_request(request):
    raw = request.params.get("id") if getattr(request, "params", None) else None
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _student_list_sql():
    return """
        SELECT s.id, s.full_name, s.status, d.id AS department_id, d.name AS department_name
        FROM students s
        JOIN departments d ON d.id = s.department_id
        ORDER BY s.full_name
    """


def _student_detail_sql():
    return """
        SELECT s.id, s.full_name, s.email, s.birth_date, s.status,
               d.id AS department_id, d.name AS department_name
        FROM students s
        JOIN departments d ON d.id = s.department_id
        WHERE s.id = %s
    """


def _student_courses_sql():
    return """
        SELECT c.id, c.title
        FROM student_courses sc
        JOIN courses c ON c.id = sc.course_id
        WHERE sc.student_id = %s
        ORDER BY c.title
    """


def _student_hierarchy_sql():
    return """
        WITH RECURSIVE ancestors AS (
            SELECT d.id, d.name, d.parent_id, 0 AS depth
            FROM departments d
            WHERE d.id = %s
            UNION ALL
            SELECT p.id, p.name, p.parent_id, a.depth + 1
            FROM departments p
            JOIN ancestors a ON p.id = a.parent_id
        )
        SELECT name, depth
        FROM ancestors
        ORDER BY depth DESC
    """


def _student_profile_sql():
    return """
        SELECT student_id, phone, emergency_contact, notes
        FROM student_profiles
        WHERE student_id = %s
    """


def _course_detail_sql():
    return """
        SELECT c.id, c.title, c.credits, c.schedule,
               t.id AS teacher_id, t.full_name AS teacher_name
        FROM courses c
        JOIN teachers t ON t.id = c.teacher_id
        WHERE c.id = %s
    """


def _course_students_sql():
    return """
        SELECT s.id, s.full_name
        FROM student_courses sc
        JOIN students s ON s.id = sc.student_id
        WHERE sc.course_id = %s
        ORDER BY s.full_name
    """


def student_list_en(request):
    rows = db.fetch_all(_student_list_sql())
    items = []
    for row in rows:
        items.append(
            f'<li><a href="/student/{row["id"]}/en">{_escape(row["full_name"])}</a>'
            f' — {_escape(row["department_name"])}</li>'
        )
    body = "<h1>Students</h1><ul>" + "".join(items) + "</ul>"
    return HTMLResponse(body)


def student_detail_en(request):
    student_id = _student_id_from_request(request)
    if student_id is None:
        return None

    student_rows = db.fetch_all(_student_detail_sql(), (student_id,))
    if not student_rows:
        return HTMLResponse("Not Found", status=404)

    student = student_rows[0]
    course_rows = db.fetch_all(_student_courses_sql(), (student_id,))
    hierarchy_rows = db.fetch_all(_student_hierarchy_sql(), (student["department_id"],))
    profile_rows = db.fetch_all(_student_profile_sql(), (student_id,))

    course_html = "".join(
        f'<li>{_escape(row["title"])}</li>' for row in course_rows
    ) or "<li>No courses</li>"
    trail = " › ".join(_escape(row["name"]) for row in hierarchy_rows)
    profile_html = ""
    if profile_rows:
        profile = profile_rows[0]
        profile_html = (
            "<h2>Student profile</h2>"
            f"<p>Phone: {_escape(profile['phone'])}</p>"
            f"<p>Emergency contact: {_escape(profile['emergency_contact'])}</p>"
            f"<p>Notes: {_escape(profile['notes'])}</p>"
        )

    html = (
        "<h1>{name}</h1>"
        "<p>Email: {email}</p>"
        "<p>Status: {status}</p>"
        "<p>Department: {department}</p>"
        "<p>Path: {trail}</p>"
        "<h2>Courses</h2><ul>{courses}</ul>{profile}"
    ).format(
        name=_escape(student["full_name"]),
        email=_escape(student["email"]),
        status=_escape(student["status"]),
        department=_escape(student["department_name"]),
        trail=trail or "No department trail",
        courses=course_html,
        profile=profile_html,
    )
    return HTMLResponse(html)


def course_detail_en(request):
    course_id = _student_id_from_request(request)
    if course_id is None:
        return None

    course_rows = db.fetch_all(_course_detail_sql(), (course_id,))
    if not course_rows:
        return HTMLResponse("Not Found", status=404)

    course = course_rows[0]
    student_rows = db.fetch_all(_course_students_sql(), (course_id,))

    student_html = "".join(
        f'<li><a href="/student/{row["id"]}/en">{_escape(row["full_name"])}</a></li>'
        for row in student_rows
    ) or "<li>No students</li>"

    html = (
        "<h1>{title}</h1>"
        "<p>Teacher: {teacher}</p>"
        "<p>Credits: {credits}</p>"
        "<p>Schedule: {schedule}</p>"
        "<h2>Students</h2><ul>{students}</ul>"
    ).format(
        title=_escape(course["title"]),
        teacher=_escape(course["teacher_name"]),
        credits=_escape(course["credits"]),
        schedule=_escape(course["schedule"]),
        students=student_html,
    )
    return HTMLResponse(html)


def student_extra_form(request):
    student_id = _student_id_from_request(request)
    if student_id is None:
        return None
    has_profile = db.fetch_all(_student_profile_sql(), (student_id,))
    if not has_profile:
        return HTMLResponse(
            "<form method='post'><input name='phone' value=''><input name='emergency_contact' value=''><textarea name='notes'></textarea><button type='submit'>Save</button></form>"
        )
    return HTMLResponse("Profile already exists", status=400)


def student_extra_post(request):
    student_id = _student_id_from_request(request)
    if student_id is None:
        return None

    student_rows = db.fetch_all(_student_detail_sql(), (student_id,))
    if not student_rows:
        return HTMLResponse("Not Found", status=404)

    form = dict(parse_qsl(request.body or "", keep_blank_values=True))
    phone = (form.get("phone") or "").strip()
    emergency_contact = (form.get("emergency_contact") or "").strip()
    notes = (form.get("notes") or "").strip()

    if len(phone) < 3 or len(phone) > 30 or len(emergency_contact) < 3 or len(emergency_contact) > 120:
        return HTMLResponse("Bad Request", status=400)

    if db.fetch_all(_student_profile_sql(), (student_id,)):
        return HTMLResponse("Profile already exists", status=400)

    db.execute(
        "INSERT INTO student_profiles (student_id, phone, emergency_contact, notes) VALUES (%s, %s, %s, %s)",
        (student_id, phone, emergency_contact, notes),
    )
    return RedirectResponse(f"/student/{student_id}/en")


def department_tree_en(request):
    rows = db.fetch_all(
        """
        WITH RECURSIVE tree AS (
            SELECT id, name, parent_id, 0 AS depth, name AS path
            FROM departments
            WHERE parent_id IS NULL
            UNION ALL
            SELECT d.id, d.name, d.parent_id, t.depth + 1, t.path || ' > ' || d.name
            FROM departments d
            JOIN tree t ON d.parent_id = t.id
        )
        SELECT * FROM tree ORDER BY path
        """
    )
    items = "".join(f'<li>{"  " * (row["depth"] + 1)}{_escape(row["name"])}</li>' for row in rows)
    return HTMLResponse(f"<h1>Departments</h1><ul>{items}</ul>")


def department_detail_en(request):
    dept_id = _student_id_from_request(request)
    if dept_id is None:
        return None
    rows = db.fetch_all("SELECT id, name, description FROM departments WHERE id = %s", (dept_id,))
    if not rows:
        return HTMLResponse("Not Found", status=404)
    department = rows[0]
    child_rows = db.fetch_all("SELECT id, full_name FROM students WHERE department_id = %s ORDER BY full_name", (dept_id,))
    child_html = "".join(f'<li><a href="/student/{row["id"]}/en">{_escape(row["full_name"])}</a></li>' for row in child_rows) or "<li>No students</li>"
    return HTMLResponse(f"<h1>{_escape(department['name'])}</h1><p>{_escape(department['description'])}</p><ul>{child_html}</ul>")


def home(request):
    return app._render_home(request, "en")


def reset(request):
    return app.handle_reset(request)


def logout(request):
    return app.handle_logout(request)


def login(request):
    return app.login_form()


def login_post(request):
    form = parse_query_string(request.body or "")
    username = form.get("username") or ""
    password = form.get("password") or ""
    if not check_password(username, password):
        return app.login_form(error="Login failed")

    role = "admin" if username == "admin" else "user"
    email = USERS.get(username, {}).get("email")
    session_id = create_session({"user": username, "role": role, "email": email})
    response = RedirectResponse("/profile")
    response.set_cookie("session_id", session_id, max_age=3600, http_only=True)
    return response


def profile(request):
    session_id = (request.cookies or {}).get("session_id")
    session = sessions.get_session(session_id) if session_id else None
    if session is None:
        return RedirectResponse("/login")
    profile_data = {
        "user": session.get("user"),
        "role": session.get("role"),
        "email": session.get("email"),
    }
    return app._render_page("profile", request, profile_data)


def api_login(request):
    form = parse_query_string(request.body or "")
    username = form.get("username") or ""
    password = form.get("password") or ""
    if not check_password(username, password):
        return JSONResponse({"error": "invalid_credentials"}, status=401)
    role = "admin" if username == "admin" else "user"
    return JSONResponse({"token": make_token(username, role)})


def api_profile(request):
    auth = (request.headers or {}).get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return JSONResponse({"error": "missing_authorization"}, status=401)
    payload = verify_token(auth.split(None, 1)[1])
    if payload is None:
        return JSONResponse({"error": "invalid_token"}, status=401)
    return JSONResponse({"user": payload.get("username"), "role": payload.get("role")})


def admin(request):
    session_id = (request.cookies or {}).get("session_id")
    session = sessions.get_session(session_id) if session_id else None
    role = session.get("role") if session is not None else (request.cookies or {}).get("role")
    if session_id is None and role is None:
        return RedirectResponse("/login")
    if role != "admin":
        return HTMLResponse("403 Forbidden", status=403)
    return HTMLResponse("Welcome to admin area")


def about(request):
    return app._render_page("about", request)


def demo(request):
    return app._render_page("demo", request)


def echo_get(request):
    return app._render_page("demo", request)


def echo_post(request):
    return Response(request.body or "", content_type="text/plain; charset=utf-8")


def students_list_en(request):
    return student_list_en(request)


def courses_list_en(request):
    rows = db.fetch_all(
        """
        SELECT c.id, c.title, t.full_name AS teacher_name
        FROM courses c
        JOIN teachers t ON t.id = c.teacher_id
        ORDER BY c.title
        """
    )
    items = "".join(
        f'<li><a href="/course/{row["id"]}/en">{_escape(row["title"])}</a> — {_escape(row["teacher_name"])}</li>'
        for row in rows
    )
    return HTMLResponse("<h1>Courses</h1><ul>" + items + "</ul>")


def student_detail(request):
    return student_detail_en(request)


def course_detail(request):
    return course_detail_en(request)


def student_extra_get(request):
    return student_extra_form(request)


def student_extra(request):
    return student_extra_post(request)


def departments_tree(request):
    return department_tree_en(request)


def department_page(request):
    return department_detail_en(request)


def home_lang(request):
    lang = request.params["lang"]
    if lang not in {"en", "ua"}:
        return HTMLResponse("Not Found", status=404)
    return app._render_home(request, lang)


def localized_page(request):
    code = request.params["code"]
    lang = request.params["lang"]
    if code not in {"index", "about", "demo"} or lang not in {"en", "ua"}:
        return HTMLResponse("Not Found", status=404)
    if code == "index":
        return app._render_home(request, lang)
    return app._render_page(code, request, lang=lang)


ROUTE_TABLE = [
    ("GET", "/", "home"),
    ("GET", "/reset", "reset"),
    ("GET", "/logout", "logout"),
    ("GET", "/login", "login"),
    ("POST", "/login", "login_post"),
    ("GET", "/profile", "profile"),
    ("POST", "/api/login", "api_login"),
    ("GET", "/api/profile", "api_profile"),
    ("GET", "/admin", "admin"),
    ("GET", "/about", "about"),
    ("GET", "/demo", "demo"),
    ("GET", "/echo", "echo_get"),
    ("POST", "/echo", "echo_post"),
    ("GET", "/students/en", "students_list_en"),
    ("GET", "/student/{id}/en", "student_detail"),
    ("GET", "/student/{id}/en/extra", "student_extra_get"),
    ("POST", "/student/{id}/en/extra", "student_extra"),
    ("GET", "/courses/en", "courses_list_en"),
    ("GET", "/course/{id}/en", "course_detail"),
    ("GET", "/departments/en", "departments_tree"),
    ("GET", "/department/{id}/en", "department_page"),
    ("GET", "/{lang}", "home_lang"),
    ("GET", "/{code}/{lang}", "localized_page"),
]


def register_routes(app_instance):
    if getattr(app_instance, "_routes_loaded", False):
        return
    for method, pattern, handler_name in ROUTE_TABLE:
        handler = globals().get(handler_name)
        if handler is not None:
            app_instance.router.add_route(method, pattern, handler)
    app_instance._routes_loaded = True
