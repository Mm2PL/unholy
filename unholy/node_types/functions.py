import ast
import typing
import warnings

import unholy
from typechecker import ensure_typecheck

@ensure_typecheck
def jsify_function_definition(node: typing.Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> typing.List[unholy.Compilable]:
    name = node.name
    decorators = []
    for i in node.decorator_list:
        decorators.extend(unholy.jsify_node(i))
        decorators.append('(')

    if decorators:
        decorators.pop(-1)  # remove unnecessary '('

    arguments: typing.List[ast.arg] = node.args.args
    arg_list = ', '.join([i.arg for i in arguments])
    if node.args.kwarg:
        arg_list += f', options'
    if node.args.vararg:
        arg_list += f', ...{node.args.vararg.arg}'
    body = []
    for i in node.body:
        body.extend(unholy.jsify_node(i))
    if isinstance(node, ast.FunctionDef):
        keyword = 'function'
    elif isinstance(node, ast.AsyncFunctionDef):
        keyword = 'async function'
    else:
        raise unholy.CompilationError('Expected a FunctionDev or AsyncFunctionDef. Something broke.')
    return [
        # unholy.JSStatement(f'let {name} = {decorators}(function {name}({arg_list})', has_semicolon=False),
        unholy.JSStatement('let ', [
            name,
            ' = ',
            *decorators,
            f'({keyword}',
            name,
            '(',
            arg_list,
            ')'
        ], has_semicolon=False),
        unholy.JSBlock(body),
        unholy.JSStatement(')' * (len(node.decorator_list) + 1), force_concat=True)
    ]


@ensure_typecheck
def jsify_return(node: ast.Return) -> typing.List[unholy.Compilable]:
    # 'value',
    # noinspection PyTypeChecker
    v: unholy.JSStatement = unholy.jsify_node(node.value)[0]
    v.force_concat = True
    return [
        unholy.JSStatement(f'return'),
        v
    ]


@ensure_typecheck
def jsify_lambda(node: ast.Lambda) -> typing.List[unholy.Compilable]:
    # args, body
    arguments: typing.List[ast.arg] = node.args.args
    arg_list = ', '.join([i.arg for i in arguments])
    if node.args.kwarg:
        arg_list += f', options'
    if node.args.vararg:
        arg_list += f', ...{node.args.vararg.arg}'
    return [
        unholy.JSExpression([
            unholy.JSExpression([f'({arg_list}) =>']),
            unholy.JSBlock(unholy.jsify_node(node.body))
        ])
    ]


@ensure_typecheck
def jsify_call(node: ast.Call) -> typing.List[unholy.Compilable]:
    func_name = unholy.jsify_node(node.func)
    args = []
    for i in node.args:
        args.extend(unholy.jsify_node(i))

    if node.keywords:
        warnings.warn(f'keyword arguments were ignored while calling {func_name}')
    return [unholy.JSExpression([
        func_name[0],
        '(',
        *args,
        ')'
    ])]


__all__ = ['jsify_lambda', 'jsify_return', 'jsify_function_definition', 'jsify_call']
