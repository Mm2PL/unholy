import abc
from typing import List, Union, Optional

from typechecker import typecheck

INDENT = '    '


class Compilable(abc.ABC):
    @abc.abstractmethod
    def compile(self, lines_ref: List[str], indent: int = 0, indent_inc: int = 1) -> str:
        """
        Compiles and indents the Compilable.
        :param indent: How much to indent the output
        :param indent_inc: How indent should change in inner blocks.
        :return:
        """
        pass

    def _indent_line(self, line: str, count: int) -> str:
        return INDENT * count + line

    def _indent_code(self, lines: str, count: int) -> str:
        out = []
        for i in lines.split('\n'):
            out.append(self._indent_line(i, count))
        return '\n'.join(out)


class JSExpression(Compilable):
    def __init__(self, others: List[Union['JSExpression', str]]):
        typecheck({
            'others': List[Union[JSExpression, str]]
        }, others=others)
        self.others = others

    def compile(self, lines_ref: List[str], indent: int = 0, indent_inc: int = 1) -> str:
        typecheck({
            'lines_ref': List[str],
            'indent': int,
            'indent_inc': int
        }, lines_ref=lines_ref, indent=indent, indent_inc=indent_inc)

        output = ''
        for i in self.others:
            if isinstance(i, Compilable):
                output += i.compile(lines_ref, indent, indent_inc)
            elif isinstance(i, str):
                output += i
            elif isinstance(i, int):
                output += str(i)
            else:
                raise RuntimeError(f'{self}: unable to compile {i!r} as a part of a JS expression')
        return output

    def __repr__(self):
        return f'{self.__class__.__name__}({self.others!r})'


class JSStatement(JSExpression, Compilable):
    def __init__(self, expr: Union[Compilable, str], others: Optional[List[Union[Compilable, str]]] = None,
                 has_semicolon=True, force_concat=False):
        typecheck({
            'expr': Union[JSExpression, str],
            'others': Optional[List[Union[JSExpression, str]]],
            'has_semicolon': bool,
            'force_concat': bool,
        }, others=others, expr=expr, has_semicolon=has_semicolon, force_concat=force_concat)

        if others:
            o = others.copy()
        else:
            o = []
        o.insert(0, expr)
        super().__init__(o or [expr])
        self.has_semicolon = has_semicolon
        self.force_concat = force_concat

    def compile(self, lines_ref: List[str], indent: int = 0, indent_inc: int = 1):
        o = super().compile(lines_ref, indent, indent_inc)
        return self._indent_code((o.rstrip(';') + ';') if self.has_semicolon else o, count=indent)


class JSBlock(Compilable):
    def __init__(self, statements, has_braces=True):
        self.statements = statements
        self.has_braces = has_braces

    def compile(self, lines_ref: List[str], indent: int = -1, indent_inc: int = 1):
        output = []
        if self.has_braces:
            if lines_ref and not lines_ref[-1].endswith(';'):
                lines_ref[-1] += ' {'
            else:
                output.append('{')

        for i, elem in enumerate(self.statements):
            s = elem.compile(output, indent + indent_inc, indent_inc)
            if isinstance(elem, JSStatement) and elem.force_concat:
                output[-1] += s
            else:
                output.append(s)

        if self.has_braces:
            output.append('}')
        return self._indent_code('\n'.join(output), indent)

    def __repr__(self):
        return f'<JSBlock: {repr(self.statements[0]) if self.statements else "no statements"}>'


class CompilationError(NotImplementedError):
    pass


if __name__ == '__main__':
    # test = JSBlock([
    #     JSStatement('(iterable) =>', has_semicolon=False),
    #     JSBlock(
    #         [
    #             JSStatement('for (const i of iterable)', has_semicolon=False),
    #             JSBlock(
    #                 [
    #                     JSStatement('console.log(i)')
    #                 ]
    #             )
    #         ]
    #     ),
    #
    #     JSStatement('console.log("test")'),
    #     JSBlock([
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")'),
    #         JSStatement('console.log("this is a block")')
    #     ])
    # ], False)
    decorators = 'a_decorator('
    name = 'a_function'
    arg_list = ''

    # test = JSBlock([
    #     JSStatement(f'let {name} = {decorators}(function {name}({arg_list})', has_semicolon=False),
    #     JSBlock([
    #         JSStatement('console.log("test")'),
    #         JSStatement('console.log("test")'),
    #         JSStatement('console.log("test")'),
    #         JSStatement('console.log("test")')
    #     ]),
    #     JSStatement(')' * (1 + 1), force_concat=True)
    # ], False)
    test = JSBlock([
        JSStatement('let', [
            JSExpression([
                name, ' = ', decorators, '(function', name, '(', arg_list, ')'
            ])
        ], has_semicolon=False)
    ])
    print(test.compile([]))
