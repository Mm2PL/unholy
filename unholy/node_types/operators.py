import ast
from typing import List

# noinspection PyUnresolvedReferences
from typechecker import ensure_typecheck
from unholy import jsify_node
# noinspection PyUnresolvedReferences
from unholy.classes import Compilable, CompilationError, JSExpression

PY_TO_JS_OPERATORS = {
    ast.Mult: lambda l, r: JSExpression([
        *jsify_node(l),
        '*',
        *jsify_node(r),
    ]),
    ast.Div: lambda l, r: JSExpression([
        *jsify_node(l),
        '/',
        *jsify_node(r),
    ]),
    ast.Add: lambda l, r: JSExpression([
        *jsify_node(l),
        '+',
        *jsify_node(r),
    ]),
    ast.Pow: lambda l, r: JSExpression([
        *jsify_node(l),
        '**',
        *jsify_node(r),
    ]),
    ast.USub: lambda l, r: JSExpression([
        '-',
        *jsify_node(l),
    ]),
    ast.In: lambda l, r: JSExpression([
        '(',
        *jsify_node(r),
        ').contains(',
        *jsify_node(l),
        ')'
    ]),
}


@ensure_typecheck
def _jsify_operator(node, left, right, node_type_name=''):
    node_type = type(node.op)
    try:
        return [PY_TO_JS_OPERATORS[node_type](left, right)]
    except KeyError as e:
        raise CompilationError(f'no known way to compile {node_type_name}operator {node_type}') from e


@ensure_typecheck
def jsify_binop(node: ast.BinOp) -> List[Compilable]:
    return _jsify_operator(node, node.left, node.right, 'binop ')


@ensure_typecheck
def jsify_unary(node: ast.UnaryOp) -> List[Compilable]:
    return _jsify_operator(node, node.operand, None, 'unary ')


@ensure_typecheck
def jsify_comparison(node: ast.Compare) -> List[Compilable]:
    # left, ops, comparators,
    left_most = node.left
    values = node.comparators
    out = []
    left = left_most
    for num, val in enumerate(values):
        right = val
        oper = type(node.ops[num])

        try:
            out.append(PY_TO_JS_OPERATORS[oper](left, right))
        except KeyError as e:
            raise CompilationError(f'no known way to compile comparison operator {oper}') from e

        left = right

    new_out = []
    for i in out:
        new_out.append(JSExpression(['&&']))
        new_out.append(i)

    new_out.pop(0)  # remove leading '&&'
    return [JSExpression(new_out)]


__all__ = ['jsify_binop', 'jsify_unary', 'jsify_comparison']
