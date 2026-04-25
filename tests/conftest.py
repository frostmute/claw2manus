import sys
from unittest.mock import MagicMock

class MockYAMLError(Exception):
    pass

class MockYAML(MagicMock):
    YAMLError = MockYAMLError

sys.modules['yaml'] = MockYAML()
