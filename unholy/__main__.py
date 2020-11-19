import ast
import json
import logging
import warnings
import typing
from typing import Dict, List

from typechecker import ensure_typecheck
from .classes import JSBlock, Compilable, JSStatement, JSExpression, CompilationError
from .constants import START_COMMENT


@ensure_typecheck
def jsify(code: str, filename='eval.py') -> List[Compilable]:
    tree = ast.parse(code, filename, 'exec')
    # logging.debug(ast.dump(tree, annotate_fields=True, include_attributes=True, indent=4))
    return _jsify_node(tree)


PY_TO_JS_NAMES: Dict[str, str] = {
    'print': 'console.log',
    'asyncio.create_task': '',
    'asyncio.ensure_future': '',

    'format': 'unholy_js.py__format',
    'iter': 'unholy_js.py__iter',
    'next': 'unholy_js.py__next',

    'range': 'unholy_js.py__range'
}
PY_TO_JS_OPERATORS = {
    ast.Mult: lambda l, r: JSExpression([
        *_jsify_node(l),
        '*',
        *_jsify_node(r),
    ]),
    ast.Div: lambda l, r: JSExpression([
        *_jsify_node(l),
        '/',
        *_jsify_node(r),
    ]),
    ast.Add: lambda l, r: JSExpression([
        *_jsify_node(l),
        '+',
        *_jsify_node(r),
    ]),
    ast.Pow: lambda l, r: JSExpression([
        *_jsify_node(l),
        '**',
        *_jsify_node(r),
    ]),
    ast.USub: lambda l, r: JSExpression([
        '-',
        *_jsify_node(l),
    ]),
    ast.In: lambda l, r: JSExpression([
        '(',
        *_jsify_node(r),
        ').contains(',
        *_jsify_node(l),
        ')'
    ]),
}


def _map_name(name: str) -> str:
    if name in PY_TO_JS_NAMES:
        return PY_TO_JS_NAMES[name]
    else:
        return name


def _make_function_call(fname: str, *args: str):
    return f'{fname}({args})'


def _jsify_containers(node) -> List[Compilable]:
    if isinstance(node, ast.Tuple):
        elts = []
        for i in node.elts:
            v = _jsify_node(i)
            if len(v) != 1:
                raise CompilationError(f'Expected only one JSExpression (or Compilable) while got {len(v)}: {v!r}')
            elts.append(v[0])
            elts.append(', ')

        return [JSExpression([
            '#[',
            JSExpression(elts),
            ']'
        ])]
    elif isinstance(node, ast.List):
        elts = []
        for i in node.elts:
            v = _jsify_node(i)
            if len(v) != 1:
                raise CompilationError(f'Expected only one JSExpression (or Compilable) while got {len(v)}: {v!r}')
            elts.append(v[0])
            elts.append(', ')

        return [JSExpression([
            '[',
            JSExpression(elts),
            ']'
        ])]
    elif isinstance(node, ast.Set):
        elts = []
        for i in node.elts:
            v = _jsify_node(i)
            if len(v) != 1:
                raise CompilationError(f'Expected only one JSExpression (or Compilable) while got {len(v)}: {v!r}')
            elts.append(v[0])
            elts.append(', ')

        return [JSExpression([
            'new Set(',
            JSExpression(elts),
            ')'
        ])]
    elif isinstance(node, ast.Dict):
        # keys, values
        output = []
        for k, v in zip(node.keys, node.values):
            jk = _jsify_node(k)
            jv = _jsify_node(v)
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


def _jsify_operators(node) -> List[JSExpression]:
    if isinstance(node, ast.BinOp):
        node_type = type(node.op)
        try:
            return [PY_TO_JS_OPERATORS[node_type](node.left, node.right)]
        except KeyError as e:
            raise CompilationError(f'no known way to compile operator {node_type}') from e
    elif isinstance(node, ast.UnaryOp):
        node_type = type(node.op)
        try:
            return [PY_TO_JS_OPERATORS[node_type](node.operand, None)]
        except KeyError as e:
            raise CompilationError(f'no known way to compile unary operator {node_type}') from e
    elif isinstance(node, ast.Compare):
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


def _jsify_functions(node) -> List[Compilable]:
    if isinstance(node, ast.Lambda):
        # args, body
        arguments: typing.List[ast.arg] = node.args.args
        arg_list = ', '.join([i.arg for i in arguments])
        if node.args.kwarg:
            arg_list += f', options'
        if node.args.vararg:
            arg_list += f', ...{node.args.vararg.arg}'
        return [
            JSExpression([
                JSExpression([f'({arg_list}) =>']),
                JSBlock(_jsify_node(node.body))
            ])
        ]
    elif isinstance(node, ast.FunctionDef):
        name = node.name
        decorators = []
        for i in node.decorator_list:
            decorators.extend(_jsify_node(i))
            decorators.append('(')

        if decorators:
            decorators.pop(-1)  # remove unnecessary '('

        arguments: typing.List[ast.arg] = node.args.args
        arg_list = ', '.join([i.arg for i in arguments])
        if node.args.kwarg:
            arg_list += f', options'
        if node.args.vararg:
            arg_list += f', ...{node.args.vararg.arg}'
        # return [f'let {name} = {decorators}(function {name}({arg_list}) {{',
        #         body, f'}}){")" * len(node.decorator_list)};']

        body = []
        for i in node.body:
            body.extend(_jsify_node(i))

        return [
            # JSStatement(f'let {name} = {decorators}(function {name}({arg_list})', has_semicolon=False),
            JSStatement('let ', [
                name,
                ' = ',
                *decorators,
                '(function ',
                name,
                '(',
                arg_list,
                ')'
            ], has_semicolon=False),
            JSBlock(body),
            JSStatement(')' * (len(node.decorator_list) + 1), force_concat=True)
        ]
    elif isinstance(node, ast.AsyncFunctionDef):
        name = node.name
        decorators = '('.join([_jsify_node(i) for i in node.decorator_list])
        body = [_jsify_node(i) for i in node.body]
        arguments: typing.List[ast.arg] = node.args.args
        arg_list = ', '.join([i.arg for i in arguments])
        if node.args.kwarg:
            arg_list += f', options'
            if node.args.kwarg.arg != 'options':
                body.insert(0, f'const {node.args.kwarg.arg} = options')  # nice js body will insert semicolons
        if node.args.vararg:
            arg_list += f', ...{node.args.vararg.arg}'
        # return [f'let {name} = {decorators}(async function {name}({arg_list}) {{', body,
        #         f'}}){")" * len(node.decorator_list)};']
        return [
            JSStatement(f'let {name} = {decorators}(async function {name}({arg_list})', has_semicolon=False),
            JSBlock(_jsify_node(node.body)),
            JSStatement(')' * (len(node.decorator_list) + 1), force_concat=True)
        ]
    elif isinstance(node, ast.Return):
        # 'value',
        # noinspection PyTypeChecker
        v: JSStatement = _jsify_node(node.value)[0]
        v.force_concat = True
        return [
            JSStatement(f'return'),
            v
        ]


@ensure_typecheck
def _jsify_node(node) -> List[Compilable]:
    logging.debug(f'Process node {node}')
    if isinstance(node, (ast.Tuple, ast.List, ast.Dict)):
        return _jsify_containers(node)
    elif isinstance(node, (ast.BinOp, ast.UnaryOp, ast.Compare)):
        return _jsify_operators(node)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.Return)):
        return _jsify_functions(node)

    elif isinstance(node, ast.Module):
        body = []
        for i in node.body:
            body.extend(_jsify_node(i))
        logging.debug(body)
        return [JSBlock([
            JSStatement('const unholy_js = require("./not_python/unholy_js.js")'),
            *body
        ], has_braces=False)]
    elif isinstance(node, ast.Expr):
        # 'value',
        return _jsify_node(node.value)
    elif isinstance(node, ast.Num):  # <number>
        return [JSExpression([str(node.n)])]
    elif isinstance(node, ast.Constant):
        return [JSExpression([json.dumps(node.value)])]
    elif isinstance(node, ast.Name):
        logging.debug(f'asdf {_map_name(node.id)=}')
        return [JSExpression([_map_name(node.id)])]
    elif isinstance(node, ast.Call):
        func_name = _jsify_node(node.func)
        args = []
        for i in node.args:
            args.extend(_jsify_node(i))

        if node.keywords:
            warnings.warn(f'keyword arguments were ignored while calling {func_name}')
        return [JSExpression([
            func_name[0],
            '(',
            *args,
            ')'
        ])]
    elif isinstance(node, ast.Attribute):
        # value, attr, ctx
        return [JSExpression([
            *_jsify_node(node.value),
            '.',
            node.attr
        ])]
    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
        # targets?, value, type_comment
        if isinstance(node, ast.Assign):
            t = node.targets
        else:
            t = [node.target]

        targets = []

        for i in t:
            targets.extend(_jsify_node(i))
        if len(targets) == 1:
            return [JSExpression([
                targets[0], ' = ',
                *_jsify_node(node.value)
            ])]
        else:
            output = ['[']
            for i in targets:
                output.append(i)
                output.append(', ')
            output.append('] =')
            output.extend(_jsify_node(node.value))
            return [JSExpression(output)]
    elif isinstance(node, ast.Delete):
        # 'targets',
        return [JSStatement('delete ', _jsify_node(i)) for i in node.targets]
    elif isinstance(node, ast.Subscript):
        # value, slice, ctx,
        v = _jsify_node(node.value)
        # node.slice: typing.Union[ast.Slice, ast.Index]
        if isinstance(node.slice, ast.Slice):
            raise CompilationError('Slicing is not yet implemented')
        elif isinstance(node.slice, ast.Index):
            return [JSExpression([
                *v,
                *_jsify_node(node.slice.value)
            ])]
        elif isinstance(node.slice, (ast.Constant, ast.Name)):
            return [JSExpression([*v, '[', *_jsify_node(node.slice), ']'])]
        else:
            raise CompilationError(f'Unknown index type: {type(node.slice)}. No way to js-ify. Aborting')
    elif isinstance(node, ast.Await):
        return [JSExpression([
            'await',
            *_jsify_node(node.value)
        ])]
    elif isinstance(node, ast.ImportFrom):
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

    elif isinstance(node, ast.Import):
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
    elif isinstance(node, ast.JoinedStr):  # f''
        values = []
        for i in node.values:
            if isinstance(i, ast.FormattedValue):
                values.append(JSExpression(
                    ['${', *_jsify_node(i), '}']
                ))
            else:
                if isinstance(i, ast.Constant):
                    values.append(JSExpression([i.value]))
                else:
                    values.extend(_jsify_node(i))

        return [JSExpression([
            '`',
            *values,
            '`'
        ])]
    elif isinstance(node, ast.FormattedValue):
        value = _jsify_node(node.value)
        if node.format_spec:
            fspec = _jsify_node(node.format_spec)
            return [JSExpression([
                'unholy_js.py__format(',
                *value,
                ', ',
                *fspec,
                ')'
            ])]
        else:
            return value
    elif isinstance(node, ast.If):
        # test, body, orelse,
        body = []
        for i in node.body:
            body.extend(_jsify_node(i))
        return [
            JSStatement('if ', ['(', *_jsify_node(node.test), ')'], has_semicolon=False),
            JSBlock(body)
        ]
    elif isinstance(node, ast.For):
        return _jsify_for_loop(node)
    else:
        raise CompilationError(f'Unknown node type: {type(node)!r}.')


def _parse_range_arguments(call: ast.Call):
    if len(call.args) == 1:
        return [JSExpression(['0'])], _jsify_node(call.args[0]), [JSExpression(['1'])]
    elif len(call.args) == 2:
        return _jsify_node(call.args[0]), _jsify_node(call.args[1]), [JSExpression(['1'])]
    elif len(call.args) == 3:
        return _jsify_node(call.args[0]), _jsify_node(call.args[1]), _jsify_node(call.args[2])
    else:
        raise CompilationError('Bad arguments for range() function in for loop.')


def _jsify_for_loop(node: ast.For):
    # 'target', 'iter', 'body', 'orelse', 'type_comment',
    output = []
    var_name = _jsify_node(node.target)
    if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
        # range loop
        start, end, step = _parse_range_arguments(node.iter)
        output.append(
            JSStatement(
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
        iterator = _jsify_node(node.iter)
        output.append(JSStatement(
            'for ',
            [
                '(const ',
                *var_name,
                ' of ',
                f'{_map_name("iter")}(',
                *iterator,
                '))'
            ],
            has_semicolon=False
        ))
    body = []
    for i in node.body:
        body.append(JSStatement('', _jsify_node(i)))
    output.append(JSBlock(body))
    return output


def _variable_name(name: str) -> str:
    for i in ' []-,.{}':
        name = name.replace(i, '_')
    return name

if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('file', metavar='FILE', type=open)
    p.add_argument('-o', '--output', metavar='FILE', type=str, default='-', dest='output')
    p.add_argument('-q', '--quiet', '--stfu', default=0, action='count', dest='quiet')
    program_arguments = p.parse_args()

    if program_arguments.file:
        logging.basicConfig(format='%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)s] %(message)s',
                            level=(logging.INFO if program_arguments.quiet else logging.DEBUG))
        result = jsify(''.join(program_arguments.file.readlines()))
        if program_arguments.output == '-':
            print(result[0].compile([]))
        else:
            with open(program_arguments.output, 'w') as f:
                f.write(START_COMMENT)
                f.write(result[0].compile([]))

            if program_arguments.quiet < 2:
                print(f'Written result to {program_arguments.output}')
