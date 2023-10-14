import nox
from nox_poetry import Session, session

nox.options.sessions = ["test", "coverage", "lint"]


@session(python=["3.10", "3.11", "3.12"])
def test(s: Session):
    s.install(".", "pytest", "pytest-cov")
    s.env["COVERAGE_FILE"] = f".coverage.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite")


@session(python=["3.10", "3.11", "3.12"])
def test_fastapi(s: Session):
    s.install(".[fastapi]", "pytest", "pytest-cov", "httpx")
    s.env["COVERAGE_FILE"] = f".coverage.fastapi.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite", "tests/fastapi")


@session(python=["3.10", "3.11", "3.12"])
def test_numpy(s: Session):
    s.install(".[numpy]", "pytest", "pytest-cov")
    s.env["COVERAGE_FILE"] = f".coverage.numpy.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite", "tests/test_numpy.py")


@session(venv_backend="none")
def coverage(s: Session):
    s.run("coverage", "combine")
    s.run("coverage", "html")
    s.run("coverage", "xml")


@session(venv_backend="none")
def fmt(s: Session) -> None:
    s.run("ruff", "check", ".", "--select", "I", "--fix")
    s.run("black", ".")


@session(venv_backend="none")
def lint(s: Session) -> None:
    s.run("black", "--check", ".")
    s.run("ruff", "check", ".")
