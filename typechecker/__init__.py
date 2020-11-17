import functools
import inspect
import logging
import typing

enable_typecheck = False


def typecheck(types: dict, **values):
    if not enable_typecheck:
        return

    for k, good_type in types.items():
        value = values[k]
        o, msg = _really_typecheck(value, good_type, k)
        if not o:
            raise TypeCheckError(k, good_type, value, msg)


def ensure_typecheck(func):
    if not enable_typecheck:
        return func

    signature = inspect.signature(func)

    @functools.wraps(func)
    def new_func(*a, **kw):
        if not enable_typecheck:
            return func(*a, **kw)

        true_args = {}
        arg_types = {}
        for num, obj in enumerate(signature.parameters.items()):
            param_name, param = obj
            param_name: str
            param: inspect.Parameter

            if param.annotation != inspect._empty:
                arg_types[param_name] = param.annotation

            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                if param_name in kw:
                    true_args[param.name] = kw.get(param_name, param.default or None)
                else:
                    # logging.debug(f'{a=} {num=}')
                    if len(a) > num:
                        true_args[param.name] = a[num]
                    # don't typecheck defaults
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                true_args[param.name] = kw.get(param_name, param.default)
            elif param.kind == inspect.Parameter.POSITIONAL_ONLY:
                true_args[param.name] = a[num]
            else:
                logging.debug('FeelsDonkMan')

        return_value = func(*a, **kw)
        arg_types['return'] = signature.return_annotation
        true_args['return'] = return_value
        typecheck(arg_types, **true_args)
        return return_value

    return new_func


def _really_typecheck(value, good_type, name) -> typing.Tuple[bool, str]:
    if not enable_typecheck:
        return True, 'Type checking disabled.'
    # noinspection PyProtectedMember,PyUnresolvedReferences
    if isinstance(good_type, typing._GenericAlias):
        if good_type.__origin__ == typing.Union:
            for arg in good_type.__args__:
                v = _really_typecheck(value, arg, name)
                if v:
                    return True, ''
            return False, ''  # doesn't type check
        elif good_type.__origin__ == list:
            if not isinstance(value, list):
                return False, ''

            for i, elem in enumerate(value):
                v, msg = _really_typecheck(elem, good_type.__args__[0], f'{name}[{i}]')
                if not v:
                    return False, f'At element #{i}: {elem}: {msg}'
            return True, ''
        else:
            return False, ''
    else:
        return isinstance(value, good_type), ''


class TypeCheckError(TypeError):
    def __init__(self, target, good_type, bad_value, message):
        self.message = message
        self.bad_value = bad_value
        self.good_type = good_type
        self.target = target

    def __str__(self):
        if self.message:
            return (f'{self.target} doesn\'t typecheck against {self.good_type}. It\'s of type {type(self.bad_value)}. '
                    f'{self.message}. Value is: {self.bad_value!r}')
        else:
            return (f'{self.target} doesn\'t typecheck against {self.good_type}. It\'s of type {type(self.bad_value)}. '
                    f'Value is: {self.bad_value!r}')

    def __repr__(self):
        return (f'{self.__class__.__name__}(target={self.target!r}, good_type={self.good_type!r}, '
                f'bad_value={self.bad_value!r}, message={self.message!r})')
