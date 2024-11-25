from nox import options, parametrize
from nox_poetry import Session, session

options.sessions = ["test", "test_fastapi", "test_numpy", "test_ordered_set", "coverage", "lint"]


@session(python=["3.10", "3.11", "3.12", "3.13"])
def test(s: Session):
    s.install(".", "pytest", "pytest-cov")
    s.env["COVERAGE_FILE"] = f".coverage.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite")


@session(python=["3.10", "3.11", "3.12", "3.13"])
def test_fastapi(s: Session):
    s.install(".[fastapi]", "pytest", "pytest-cov", "httpx")
    s.env["COVERAGE_FILE"] = f".coverage.fastapi.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite", "tests/fastapi")


@session(python=["3.10", "3.11", "3.12", "3.13"])
def test_numpy(s: Session):
    s.install(".[numpy]", "pytest", "pytest-cov")
    s.env["COVERAGE_FILE"] = f".coverage.numpy.{s.python}"
    s.run("python", "-m", "pytest", "--cov", "serialite", "tests/test_numpy.py")


@session(python=["3.10", "3.11", "3.12", "3.13"])
def test_ordered_set(s: Session):
    s.install(".[ordered-set]", "pytest", "pytest-cov")
    s.env["COVERAGE_FILE"] = f".coverage.ordered_set.{s.python}"
    s.run(
        "python", "-m", "pytest", "--cov", "serialite", "tests/implementations/test_ordered_set.py"
    )


@session(venv_backend="none")
def coverage(s: Session):
    s.run("coverage", "combine")
    s.run("coverage", "html")
    s.run("coverage", "xml")


@session(venv_backend="none")
@parametrize("command", [["ruff", "check", "."], ["ruff", "format", "--check", "."]])
def lint(s: Session, command: list[str]):
    s.run(*command)


@session(venv_backend="none")
def format(s: Session) -> None:
    s.run("ruff", "check", ".", "--select", "I", "--fix")
    s.run("ruff", "format", ".")
