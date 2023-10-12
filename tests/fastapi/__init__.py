import pytest

try:
    import fastapi
except ImportError:
    pytest.skip("FastAPI not available", allow_module_level=True)
