import ast
import typing

from . import functions, general, containers, fstrings, control, operators


def lookup_node_translator(node):
    return translator_map[type(node)]


translator_map: typing.Dict[type, typing.Callable] = {
    # .functions
    ast.AsyncFunctionDef: functions.jsify_function_definition,
    ast.Call: functions.jsify_call,
    ast.FunctionDef: functions.jsify_function_definition,
    ast.Lambda: functions.jsify_lambda,
    ast.Return: functions.jsify_return,

    # .general
    ast.Expr: general.jsify_expr,
    ast.Module: general.jsify_module,
    ast.Constant: general.jsify_constant,
    ast.Name: general.jsify_name,
    ast.Attribute: general.jsify_attribute,
    ast.Assign: general.jsify_assign,
    ast.Delete: general.jsify_delete,
    ast.Subscript: general.jsify_subscript,
    ast.Await: general.jsify_await,

    # .containers
    ast.Dict: containers.jsify_dict,
    ast.List: containers.jsify_list,
    ast.Set: containers.jsify_set,
    ast.Tuple: containers.jsify_tuple,

    # .fstrings
    ast.FormattedValue: fstrings.jsify_formatted_value,
    ast.JoinedStr: fstrings.jsify_fstring,

    # .control
    ast.If: control.jsify_if,
    ast.For: control.jsify_for,

    # .operators
    ast.BinOp: operators.jsify_binop,
    ast.UnaryOp: operators.jsify_unary,
    ast.Compare: operators.jsify_comparison,
}
