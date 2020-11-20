import ast
import typing

# noinspection PyUnresolvedReferences
from unholy import jsify_node
# noinspection PyUnresolvedReferences
from unholy.classes import Compilable, JSStatement, CompilationError, JSBlock, JSExpression
from typechecker import ensure_typecheck


@ensure_typecheck
def jsify_import_from(node: ast.ImportFrom) -> typing.List[Compilable]:
    requires = []
    names = node.names
    for alias in names:
        alias: ast.alias
        requires.append(JSStatement('const ', [
            '{ ',
            JSExpression([alias.asname or alias.name]),
            ' }',
            ' = ',
            'require(',
            JSExpression([f'"not_python/{alias.name}.js"']),
            ')'
        ]))
    return requires


@ensure_typecheck
def jsify_import(node: ast.Import) -> typing.List[Compilable]:
    requires = []
    names = node.names
    for alias in names:
        alias: ast.alias
        requires.append(JSStatement('const ', [
            JSExpression([alias.asname or alias.name]),
            ' = ',
            'require(',
            JSExpression([f'"not_python/{alias.name}.js"']),
            ')'
        ]))
    return requires


__all__ = ['jsify_import', 'jsify_import_from']
