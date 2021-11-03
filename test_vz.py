import pytest
from vz import *
def test_any(): assert True

class TestHello:
    def test_hello(self):
        assert Object('hello').test() == '\n<object:hello>'
