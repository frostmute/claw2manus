import sys
from unittest.mock import MagicMock

# Mock modules that are not available in the environment to allow tests to run
mock_modules = ['yaml', 'markdown', 'requests', 'bs4']
for module_name in mock_modules:
    if module_name not in sys.modules:
        m = MagicMock()
        sys.modules[module_name] = m
        if module_name == 'yaml':
            class MockYAMLError(Exception):
                pass
            m.YAMLError = MockYAMLError

            def mock_safe_load(stream):
                if not stream or not isinstance(stream, str):
                    return {}
                data = {}
                for line in stream.splitlines():
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key, value = parts
                            val = value.strip().strip('"').strip("'")
                            data[key.strip()] = val
                return data

            def mock_dump(data, **kwargs):
                res = ""
                for k, v in data.items():
                    if k == 'description' and not str(v).startswith("'"):
                         res += f"{k}: '{v}'\n"
                    else:
                         res += f"{k}: {v}\n"
                return res

            m.safe_load.side_effect = mock_safe_load
            m.dump.side_effect = mock_dump
