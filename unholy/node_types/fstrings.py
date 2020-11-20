import ast
import typing

from unholy import jsify_node
from unholy.classes import Compilable, JSExpression
from typechecker import ensure_typecheck


@ensure_typecheck
def jsify_fstring(node: ast.JoinedStr) -> typing.List[Compilable]:
    values = []
    for i in node.values:
        if isinstance(i, ast.FormattedValue):
            values.append(JSExpression(
                ['${', *jsify_node(i), '}']
            ))
        else:
            if isinstance(i, ast.Constant):
                values.append(JSExpression([i.value]))
            else:
                values.extend(jsify_node(i))

    return [JSExpression([
        '`',
        *values,
        '`'
    ])]


@ensure_typecheck
def jsify_formatted_value(node: ast.FormattedValue) -> typing.List[Compilable]:
    value = jsify_node(node.value)
    if node.format_spec:
        fspec = jsify_node(node.format_spec)
        return [JSExpression([
            'unholy_js.py__format(',
            *value,
            ', ',
            *fspec,
            ')'
        ])]
    else:
        return value


__all__ = ['jsify_fstring', 'jsify_formatted_value']
