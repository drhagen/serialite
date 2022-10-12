import pytest

try:
    import fastapi  # noqa: F401
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)
