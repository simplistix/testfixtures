# Copyright (c) 2008 Simplistix Ltd
# See license.txt for license details.
"""
A sample module containing the kind of code that
TestFixtures helps with testing
"""

from datetime import datetime, date


def str_now_1():
    return str(datetime.now())

now = datetime.now


def str_now_2():
    return str(now())


def str_today_1():
    return str(date.today())

today = date.today


def str_today_2():
    return str(today())

from time import time


def str_time():
    return str(time())


class X:

    def y(self):
        return "original y"

    @classmethod
    def aMethod(cls):
        return cls

    @staticmethod
    def bMethod():
        return 2


def z():
    return "original z"


class TestClassA:
    def __init__(self, *args):
        self.args = args


class TestClassB(TestClassA):
    pass


def a_function():
    return (TestClassA(1), TestClassB(2), TestClassA(3))

someDict = dict(
    key='value',
    complex_key=[1, 2, 3],
    )
