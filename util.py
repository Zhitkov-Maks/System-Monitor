from typing import Any, Callable
from functools import wraps
import sys


def error_decorate(errors: tuple):
    """
    Декоратор принимает кортеж с исключениями для 
    обработки ошибок.
    """
    def decorate(func: Callable) -> Callable:
        """
        Декоратор принимает функцию в которой мы хотим обработать
        исключения.
        """
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Вызов непосредственно функции и обработка 
            возможных ошибок.
            """
            try:
                return func(*args, **kwargs)
            except errors as err:
                print(f"Ошибка в функции {func.__name__}: {str(err)}")
                sys.exit(1)
        return wrapper
    return decorate
