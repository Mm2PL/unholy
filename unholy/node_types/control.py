import ast
import typing

import unholy
from typechecker import ensure_typecheck


@ensure_typecheck
def jsify_if(node: ast.If) -> typing.List[unholy.Compilable]:
    # test, body, orelse,
    body = []
    for i in node.body:
        body.extend(unholy.jsify_node(i))
    return [
        unholy.JSStatement('if ', ['(', *unholy.jsify_node(node.test), ')'], has_semicolon=False),
        unholy.JSBlock(body)
    ]


@ensure_typecheck
def _parse_range_arguments(call: ast.Call):
    if len(call.args) == 1:
        return [unholy.JSExpression(['0'])], unholy.jsify_node(call.args[0]), [unholy.JSExpression(['1'])]
    elif len(call.args) == 2:
        return unholy.jsify_node(call.args[0]), unholy.jsify_node(call.args[1]), [unholy.JSExpression(['1'])]
    elif len(call.args) == 3:
        return unholy.jsify_node(call.args[0]), unholy.jsify_node(call.args[1]), unholy.jsify_node(call.args[2])
    else:
        raise unholy.CompilationError('Bad arguments for range() function in for loop.')


@ensure_typecheck
def jsify_for(node: ast.For) -> typing.List[unholy.Compilable]:
    # 'target', 'iter', 'body', 'orelse', 'type_comment',
    output = []
    var_name = unholy.jsify_node(node.target)
    if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
        # range loop
        start, end, step = _parse_range_arguments(node.iter)
        output.append(
            unholy.JSStatement(
                'for ',
                [
                    '(let ',
                    *var_name,
                    ' = ',
                    *start,
                    '; (',
                    *step,
                    ' >= 0 ? (',
                    *var_name,
                    ' < ',
                    *end,
                    ') : ',
                    *var_name,
                    ' > ',
                    *end,
                    '); ',
                    *var_name,
                    '+=',
                    *step,
                    ')'
                ],
                has_semicolon=False
            )
        )
    else:
        iterator = unholy.jsify_node(node.iter)
        output.append(unholy.JSStatement(
            'for ',
            [
                '(const ',
                *var_name,
                ' of ',
                f'{unholy.map_name("iter")}(',
                *iterator,
                '))'
            ],
            has_semicolon=False
        ))
    body = []
    for i in node.body:
        body.append(unholy.JSStatement('', unholy.jsify_node(i)))
    output.append(unholy.JSBlock(body))
    return output
