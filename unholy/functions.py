import ast
import logging
from typing import List

from typechecker import ensure_typecheck
import unholy

@ensure_typecheck
def jsify_node(node) -> List[unholy.Compilable]:
    logging.debug(f'Process node {node}')
    try:
        return unholy.lookup_node_translator(node)(node)
    except KeyError as e:
        raise unholy.CompilationError(f'Unknown node type: {type(node)!r}.') from e


def _variable_name(name: str) -> str:
    for i in ' []-,.{}':
        name = name.replace(i, '_')
    return name


@ensure_typecheck
def jsify(code: str, filename='eval.py') -> List[unholy.Compilable]:
    tree = ast.parse(code, filename, 'exec')
    # logging.debug(ast.dump(tree, annotate_fields=True, include_attributes=True, indent=4))
    return jsify_node(tree)
