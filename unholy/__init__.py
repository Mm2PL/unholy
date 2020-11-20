from typing import Dict

from .constants import *
from .utils import *
from .classes import *
from .functions import *
from .node_types import *


def map_name(name: str) -> str:
    if name in PY_TO_JS_NAMES:
        return PY_TO_JS_NAMES[name]
    else:
        return name


PY_TO_JS_NAMES: Dict[str, str] = {
    'print': 'console.log',
    'asyncio.create_task': '',
    'asyncio.ensure_future': '',

    'format': 'unholy_js.py__format',
    'iter': 'unholy_js.py__iter',
    'next': 'unholy_js.py__next',

    'range': 'unholy_js.py__range'
}
