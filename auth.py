try:
    from .response import RedirectResponse
except Exception:
    from response import RedirectResponse


def login_required(sessions):
    def decorator(handler):
        def wrapper(request):
            session_id = request.cookies.get("session_id") if hasattr(request, "cookies") else None
            session = sessions.get_session(session_id) if session_id else None
            if not session:
                return RedirectResponse("/login")
            request.session = session
            return handler(request)
        return wrapper
    return decorator
