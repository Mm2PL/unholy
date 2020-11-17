import unittest
from unittest import TestCase
import typing

from typechecker import _really_typecheck, TypeCheckError, ensure_typecheck


class TypecheckTests(TestCase):
    def test__really_typecheck_isinstance(self):
        try:
            _really_typecheck('some string', str, 'some_string')
        except TypeCheckError as e:
            self.fail(e)

    def test__really_typecheck_bad_isinstance(self):
        try:
            _really_typecheck('some string', int, 'some_nonstring')
        except TypeCheckError as e:
            self.fail(e)

    def test__really_typecheck_list_isinstance(self):
        self.assertTrue(_really_typecheck([], list, 'some_list')[0])
        self.assertTrue(_really_typecheck([], typing.List[str], 'some_empty_list')[0])
        self.assertTrue(_really_typecheck(['some string'], typing.List[str], 'some_nonempty_list')[0])
        self.assertTrue(_really_typecheck([['some string']], typing.List[typing.List[str]], 'nested_list')[0])

    def test__really_typecheck_bad_list_isinstance(self):
        self.assertFalse(_really_typecheck((), list, 'some_list')[0])
        self.assertFalse(_really_typecheck((), typing.List[str], 'some_empty_list')[0])
        self.assertFalse(_really_typecheck([123], typing.List[str], 'some_nonempty_list')[0])
        self.assertFalse(_really_typecheck([('some_string',)], typing.List[typing.List[str]], 'nested_list')[0])

    def test_ensure_typecheck(self):
        correct_signature = ensure_typecheck(_correct_signature)
        bad_return = ensure_typecheck(_bad_return)

        try:
            correct_signature(1)
        except TypeCheckError as e:
            self.fail(e)

        try:
            correct_signature('1')
        except TypeCheckError:
            pass
        else:
            self.fail("Expected exception but that didn't happen.")

        try:
            bad_return(1)
        except TypeCheckError:
            pass
        else:
            self.fail("Expected exception but that didn't happen.")

        try:
            bad_return("1")
        except TypeCheckError:
            pass
        else:
            self.fail("Expected exception but that didn't happen.")


def _correct_signature(a: int) -> int:
    return a


def _bad_return(a: int) -> int:
    # noinspection PyTypeChecker
    return str(a)


if __name__ == '__main__':
    import logging

    logging.basicConfig(format='%(asctime)s [%(levelname)s] [%(funcName)s:%(lineno)s] %(message)s', level=logging.DEBUG)
    unittest.main()
