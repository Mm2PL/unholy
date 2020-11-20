import ast
import json
import logging
import typing

# from unholy import map_name, unholy.jsify_node
import unholy
# from unholy.classes import Compilable, unholy.JSStatement, unholy.CompilationError, unholy.JSBlock, unholy.JSExpression
from typechecker import ensure_typecheck


@ensure_typecheck
def jsify_module(node: ast.Module) -> typing.List[unholy.Compilable]:
    body = []
    for i in node.body:
        body.extend(unholy.jsify_node(i))
    logging.debug(body)
    return [unholy.JSBlock([
        unholy.JSStatement('const unholy_js = require("./not_python/unholy_js.js")'),
        *body
    ], has_braces=False)]


@ensure_typecheck
def jsify_expr(node: ast.Expr) -> typing.List[unholy.Compilable]:
    # 'value',
    return unholy.jsify_node(node.value)


@ensure_typecheck
def jsify_constant(node: ast.Constant) -> typing.List[unholy.Compilable]:
    return [unholy.JSExpression([json.dumps(node.value)])]


@ensure_typecheck
def jsify_name(node: ast.Name) -> typing.List[unholy.Compilable]:
    logging.debug(f'asdf {unholy.map_name(node.id)=}')
    return [unholy.JSExpression([unholy.map_name(node.id)])]


@ensure_typecheck
def jsify_attribute(node: ast.Attribute) -> typing.List[unholy.Compilable]:
    # value, attr, ctx
    return [unholy.JSExpression([
        *unholy.jsify_node(node.value),
        '.',
        node.attr
    ])]


@ensure_typecheck
def jsify_assign(node: typing.Union[ast.Assign, ast.AnnAssign]) -> typing.List[unholy.Compilable]:
    # targets?, value, type_comment
    if isinstance(node, ast.Assign):
        t = node.targets
    else:
        t = [node.target]

    targets = []

    for i in t:
        targets.extend(unholy.jsify_node(i))
    if len(targets) == 1:
        return [unholy.JSExpression([
            targets[0], ' = ',
            *unholy.jsify_node(node.value)
        ])]
    else:
        output = ['[']
        for i in targets:
            output.append(i)
            output.append(', ')
        output.append('] =')
        output.extend(unholy.jsify_node(node.value))
        return [unholy.JSExpression(output)]


@ensure_typecheck
def jsify_delete(node: ast.Delete) -> typing.List[unholy.Compilable]:
    # 'targets',
    return [unholy.JSStatement('delete ', unholy.jsify_node(i)) for i in node.targets]


@ensure_typecheck
def jsify_subscript(node: ast.Subscript) -> typing.List[unholy.Compilable]:
    # value, slice, ctx,
    v = unholy.jsify_node(node.value)
    # node.slice: typing.Union[ast.Slice, ast.Index]
    if isinstance(node.slice, ast.Slice):
        raise unholy.CompilationError('Slicing is not yet implemented')
    elif isinstance(node.slice, ast.Index):
        return [unholy.JSExpression([
            *v,
            *unholy.jsify_node(node.slice.value)
        ])]
    elif isinstance(node.slice, (ast.Constant, ast.Name)):
        return [unholy.JSExpression([*v, '[', *unholy.jsify_node(node.slice), ']'])]
    else:
        raise unholy.CompilationError(f'Unknown index type: {type(node.slice)}. No way to js-ify. Aborting')


@ensure_typecheck
def jsify_await(node: ast.Await) -> typing.List[unholy.Compilable]:
    return [unholy.JSExpression([
        'await',
        *unholy.jsify_node(node.value)
    ])]


@ensure_typecheck
def jsify_num(node: ast.Num) -> typing.List[unholy.Compilable]:
    return [unholy.JSExpression([str(node.n)])]


__all__ = ['jsify_expr', 'jsify_module', 'jsify_name', 'jsify_assign', 'jsify_await', 'jsify_constant',
           'jsify_attribute', 'jsify_delete', 'jsify_subscript', 'jsify_num']
