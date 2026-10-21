try:
    from .server import HTTPServer
    from .templater import Templater
except Exception:
    from server import HTTPServer
    from templater import Templater

from app_instance import app

import routes


def demo_render():
    t = Templater()
    html = t.render("demo", {"name": "John", "lang": "Python"})
    print("--- Rendered demo (hardcoded) ---")
    print(html)


if __name__ == "__main__":
    demo_render()
    HTTPServer(app).start()
