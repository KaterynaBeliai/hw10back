try:
    from .response import HTMLResponse, RedirectResponse, JSONResponse
    from .response import Response
    from .templater import Templater
    from .http_parser import parse_query_string
    from .users import check_password, USERS
    from .sessions import create_session, get_session, delete_session
    from .tokens import make_token, verify_token
    from .router import Router
except Exception:
    from response import HTMLResponse, RedirectResponse, JSONResponse
    from response import Response
    from templater import Templater
    from http_parser import parse_query_string
    from users import check_password, USERS
    from sessions import create_session, get_session, delete_session
    from tokens import make_token, verify_token
    from router import Router


SUPPORTED_LANGUAGES = {"en", "ua"}
LOCALIZED_PAGES = {"index", "about", "demo"}
HOME_TEXT = {
    "en": {
        "language_label": "Language",
        "language_name": "English",
        "welcome": "Welcome to the Example Site",
        "intro": "This is the index page. Try the",
        "demo_label": "demo",
    },
    "ua": {
        "language_label": "Мова",
        "language_name": "Українська",
        "welcome": "Вітаємо на демонстраційному сайті",
        "intro": "Це головна сторінка. Спробуйте",
        "demo_label": "демо",
    },
}
UA_TRANSLATIONS = {
    '<a href="/">Home</a>': '<a href="/">Головна</a>',
    '<a href="/about">About</a>': '<a href="/about">Про сайт</a>',
    '<a href="/demo">Demo</a>': '<a href="/demo">Демо</a>',
    "<h1>About</h1>": "<h1>Про сайт</h1>",
    "This site demonstrates a tiny Python web server and a templater.": "Цей сайт демонструє невеликий вебсервер на Python і шаблонізатор.",
    "<h1>Demo</h1>": "<h1>Демо</h1>",
    "Hello, ": "Вітаємо, ",
    "! You're looking at a page about ": "! Ви переглядаєте сторінку про ",
    "You have visited this page ": "Ви відвідали цю сторінку ",
    " time(s)": " раз(ів)",
    "Message": "Повідомлення",
    "Send": "Надіслати",
    "Example site — neutral placeholder content.": "Навчальний сайт про невеликий вебсервер і шаблонізатор.",
}


class App:
    def __init__(self, pages_dir=None):
        self.templater = Templater(pages_dir)
        self.router = Router()
        self._routes_loaded = False

        try:
            import routes
            routes.app = self
            if not self._routes_loaded:
                routes.register_routes(self)
        except Exception:
            pass

    def get(self, path):
        return self._route("GET", path)

    def post(self, path):
        return self._route("POST", path)

    def _route(self, method, path):
        def decorator(handler):
            self.router.add_route(method, path, handler)
            return handler
        return decorator

    def handle(self, request):
        return self.handle_request(request)

    def handle_request(self, request):
        handler, params = self.router.match(request.method.upper(), request.path)
        if handler is None:
            return HTMLResponse("Not Found", status=404)

        request.params = params
        response = handler(request)
        if response is None:
            return HTMLResponse("Not Found", status=404)
        if isinstance(response, Response):
            return response
        if isinstance(response, (str, bytes)):
            return HTMLResponse(response if isinstance(response, str) else response.decode("utf-8", "replace"))
        return HTMLResponse(str(response))

    def login_form(self, error=""):
        html = self.templater.render("login", {"error": error})
        return HTMLResponse(html)

    def handle_home(self, request):
        return self._render_home(request, "en")

    def handle_home_lang(self, request):
        lang = request.params["lang"]
        if lang not in SUPPORTED_LANGUAGES:
            return None
        return self._render_home(request, lang)

    def handle_localized_page(self, request):
        page = request.params["code"]
        lang = request.params["lang"]
        if page not in LOCALIZED_PAGES or lang not in SUPPORTED_LANGUAGES:
            return None
        if page == "index":
            return self._render_home(request, lang)
        return self._render_page(page, request, lang=lang)

    def _render_home(self, request, lang):
        params = dict(request.query or {})
        params["lang"] = lang
        params.update(HOME_TEXT[lang])

        visits_raw = (request.cookies or {}).get("visits")
        visits = int(visits_raw) if isinstance(visits_raw, str) and visits_raw.isdigit() else 0
        params["visits"] = visits + 1

        html = self.templater.render("index", params=params)
        if html is None:
            return None
        if lang == "ua":
            html = self._translate_ua(html)

        response = HTMLResponse(html)
        response.set_cookie("visits", str(params["visits"]))
        return response

    def handle_reset(self, request):
        response = RedirectResponse("/")
        response.delete_cookie("visits")
        return response

    def handle_logout(self, request):
        session_id = (request.cookies or {}).get("session_id")
        if session_id:
            delete_session(session_id)
        response = RedirectResponse("/")
        response.delete_cookie("session_id")
        response.delete_cookie("visits")
        return response

    def handle_login(self, request):
        if request.method.upper() == "GET":
            return self.login_form()
        if request.method.upper() != "POST":
            return None

        form = parse_query_string(request.body or "")
        username = form.get("username") or ""
        password = form.get("password") or ""
        use_cookie = form.get("insecure") == "1"

        if not check_password(username, password):
            return self.login_form(error="Login failed")

        role = "admin" if username == "admin" else "user"
        email = USERS.get(username, {}).get("email")
        if use_cookie:
            response = RedirectResponse("/profile")
            response.set_cookie("user", username)
            response.set_cookie("role", role)
            response.set_cookie("email", email, max_age=3600)
            return response

        session_id = create_session({"user": username, "role": role, "email": email})
        response = RedirectResponse("/profile")
        response.set_cookie("session_id", session_id, max_age=3600, http_only=True)
        return response

    def handle_profile(self, request):
        session_id = (request.cookies or {}).get("session_id")
        session = get_session(session_id)
        if session is None:
            user = (request.cookies or {}).get("user")
            if not user:
                return RedirectResponse("/login")
            profile = {
                "user": user,
                "role": (request.cookies or {}).get("role"),
                "email": (request.cookies or {}).get("email"),
            }
        else:
            profile = {
                "user": session.get("user"),
                "role": session.get("role"),
                "email": session.get("email"),
            }
        return self._render_page("profile", request, profile)

    def handle_api_login(self, request):
        form = parse_query_string(request.body or "")
        username = form.get("username") or ""
        password = form.get("password") or ""
        if not check_password(username, password):
            return JSONResponse({"error": "invalid_credentials"}, status=401)

        role = "admin" if username == "admin" else "user"
        token = make_token(username, role)
        return JSONResponse({"token": token})

    def handle_api_profile(self, request):
        auth = (request.headers or {}).get("authorization")
        if not auth or not auth.lower().startswith("bearer "):
            return JSONResponse({"error": "missing_authorization"}, status=401)

        token = auth.split(None, 1)[1]
        payload = verify_token(token)
        if payload is None:
            return JSONResponse({"error": "invalid_token"}, status=401)
        return JSONResponse({"user": payload.get("username"), "role": payload.get("role")})

    def handle_admin(self, request):
        session_id = (request.cookies or {}).get("session_id")
        session = get_session(session_id)
        role = session.get("role") if session is not None else (request.cookies or {}).get("role")

        if session_id is None and role is None:
            return RedirectResponse("/login")
        if role != "admin":
            return HTMLResponse("403 Forbidden", status=403)
        return HTMLResponse("Welcome to admin area")

    def handle_about(self, request):
        return self._render_page("about", request)

    def handle_demo(self, request):
        return self._render_page("demo", request)

    def handle_echo(self, request):
        if request.method.upper() == "GET":
            return self._render_page("demo", request)
        if request.method.upper() == "POST":
            return Response(request.body or "", content_type="text/plain; charset=utf-8")
        return None

    def _render_page(self, name, request, params=None, lang="en"):
        template_params = dict(request.query or {})
        if name == "demo":
            template_params.setdefault("name", "Jane")
            template_params.setdefault("lang", "Python")
        if params:
            template_params.update(params)
        html = self.templater.render(name, params=template_params)
        if html is None:
            return None
        if lang == "ua":
            html = self._translate_ua(html)
        return HTMLResponse(html)

    @staticmethod
    def _translate_ua(html):
        for english, ukrainian in UA_TRANSLATIONS.items():
            html = html.replace(english, ukrainian)
        return html
