import sys
from unittest.mock import MagicMock

# Mock modules that are not available in the environment to allow tests to run.
# When a real implementation is importable (e.g. in CI or a developer machine
# with the test extra installed), we leave it alone — the mock is only a
# fallback for minimal environments where pytest is somehow available but the
# runtime deps aren't.
def _try_import(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


mock_modules = []
if not _try_import("yaml"):
    mock_modules.append("yaml")
if not _try_import("markdown"):
    mock_modules.append("markdown")
if not _try_import("requests"):
    mock_modules.append("requests")
if not _try_import("bs4"):
    mock_modules.append("bs4")

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
                    val = str(v)
                    if any(c in val for c in ":'\"[]{}#|>& "):
                        res += f"{k}: '{val}'\n"
                    else:
                        res += f"{k}: {val}\n"
                return res

            m.safe_load.side_effect = mock_safe_load
            m.dump.side_effect = mock_dump
