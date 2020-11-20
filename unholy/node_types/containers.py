import ast
from typing import List

from typechecker import ensure_typecheck
from unholy import jsify_node
from unholy.classes import Compilable, CompilationError, JSExpression


def _jsify_sequential_container(node, prefix, suffix) -> List[Compilable]:
    elts = []
    for i in node.elts:
        v = jsify_node(i)
        if len(v) != 1:
            raise CompilationError(f'Expected only one JSExpression (or Compilable) while got {len(v)}: {v!r}')
        elts.append(v[0])
        elts.append(', ')

    return [JSExpression([
        prefix,
        JSExpression(elts),
        suffix
    ])]


@ensure_typecheck
def jsify_list(node: ast.List) -> List[Compilable]:
    return _jsify_sequential_container(node, '[', ']')


@ensure_typecheck
def jsify_tuple(node: ast.Tuple) -> List[Compilable]:
    return _jsify_sequential_container(node, '#[', ']')


@ensure_typecheck
def jsify_set(node: ast.Set) -> List[Compilable]:
    return _jsify_sequential_container(node, 'new Set([', '])')


@ensure_typecheck
def jsify_dict(node: ast.Dict) -> List[Compilable]:
    # keys, values
    output = []
    for k, v in zip(node.keys, node.values):
        jk = jsify_node(k)
        jv = jsify_node(v)
        if len(jk) != 1:
            raise CompilationError(f'Dict key: Expected only one JSExpression (or Compilable) while got '
                                   f'{len(jk)}: {jk!r}')
        if len(jv) != 1:
            raise CompilationError(f'Dict value: Expected only one JSExpression (or Compilable) while got '
                                   f'{len(jv)}: {jv!r}')

        output.append(JSExpression([
            JSExpression(['[', jk[0], ']', ':']),
            jv[0],
        ]))
    return [JSExpression([
        '{',
        JSExpression(output),
        '}',
    ])]


__all__ = ['jsify_set', 'jsify_dict', 'jsify_list', 'jsify_tuple']
