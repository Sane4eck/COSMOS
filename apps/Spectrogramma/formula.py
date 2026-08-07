from __future__ import annotations

import ast
import operator
from typing import Any, Callable

import numpy as np


DEFAULT_FORMULA = "10 * log10(sxx + 1e-9)"


_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "log10": np.log10,
    "log": np.log,
    "ln": np.log,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "clip": np.clip,
    "exp": np.exp,
    "minimum": np.minimum,
    "maximum": np.maximum,
    "power": np.power,
}

_BINARY_OPERATORS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}

_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_CONSTANTS = {
    "pi": float(np.pi),
    "e": float(np.e),
}


def _function_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id

    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "np"
    ):
        return node.attr

    raise ValueError("Дозволені лише безпечні математичні функції")


def _evaluate(node: ast.AST, sxx: np.ndarray):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, sxx)

    if isinstance(node, ast.Constant):
        if node.value is None or isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("У формулі дозволені лише числові константи")

    if isinstance(node, ast.Name):
        if node.id == "sxx":
            return sxx
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError(f"Невідома змінна: {node.id}")

    if isinstance(node, ast.Attribute):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "np"
            and node.attr in _CONSTANTS
        ):
            return _CONSTANTS[node.attr]
        raise ValueError("Доступ до атрибутів заборонений")

    if isinstance(node, ast.BinOp):
        operation = _BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("Ця математична операція не підтримується")
        return operation(_evaluate(node.left, sxx), _evaluate(node.right, sxx))

    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise ValueError("Ця унарна операція не підтримується")
        return operation(_evaluate(node.operand, sxx))

    if isinstance(node, ast.Call):
        if node.keywords:
            raise ValueError("Іменовані аргументи у функціях не підтримуються")
        name = _function_name(node.func)
        function = _FUNCTIONS.get(name)
        if function is None:
            raise ValueError(f"Функція {name} не дозволена")
        arguments = [_evaluate(argument, sxx) for argument in node.args]
        return function(*arguments)

    raise ValueError(f"Конструкція {type(node).__name__} у формулі не дозволена")


def apply_spectrum_formula(
    sxx,
    formula: str | None,
) -> tuple[np.ndarray, str]:
    source = np.asarray(sxx, dtype=np.float32)
    expression = str(formula or "").strip() or DEFAULT_FORMULA

    if len(expression) > 500:
        raise ValueError("Формула занадто довга")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Некоректний синтаксис формули: {exc.msg}") from exc

    try:
        with np.errstate(all="ignore"):
            result = _evaluate(tree, source)
    except (TypeError, ValueError, FloatingPointError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith((
            "Дозволені",
            "У формулі",
            "Невідома",
            "Доступ",
            "Ця ",
            "Іменовані",
            "Функція",
            "Конструкція",
        )):
            raise
        raise ValueError(f"Не вдалося обчислити формулу: {exc}") from exc

    try:
        values = np.asarray(result, dtype=np.float32)
    except (TypeError, ValueError) as exc:
        raise ValueError("Формула повинна повертати числовий масив") from exc

    if values.shape != source.shape:
        raise ValueError(
            "Формула повинна повертати масив тієї ж форми, що й sxx"
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Формула створила NaN або нескінченні значення. "
            "Для log/log10 додайте малий epsilon або використайте clip()."
        )

    return values, expression


def spectrum_value_metadata(formula: str) -> tuple[str, str]:
    normalized = formula.replace("np.", "").replace(" ", "").lower()

    if normalized == "sxx":
        return "PSD (g²/Гц)", "g²/Гц"

    if normalized in {"sqrt(sxx)", "power(sxx,0.5)", "sxx**0.5"}:
        return "ASD (g/√Гц)", "g/√Гц"

    if "log10(" in normalized:
        return "Рівень спектра (дБ/Гц)", "дБ/Гц"

    return "Значення формули", ""
