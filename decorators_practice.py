def uppercase(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper


def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator


@uppercase
@repeat(3)
def greet_broken(name):
    return f"hello, {name}"


@repeat(3)
@uppercase
def greet_ok(name):
    return f"hello, {name}"


print(greet_ok("John"))
try:
    print(greet_broken("John"))
except AttributeError as exc:
    print(type(exc).__name__, exc)
