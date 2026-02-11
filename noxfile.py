from nox import Session, options, parametrize
from nox_uv import session

options.default_venv_backend = "uv"
options.sessions = [
    "test",
    "test_fastapi",
    "test_numpy",
    "test_ordered_set",
    "coverage",
    "lint",
    "typecheck",
]


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"])
def test(s: Session):
    coverage_file = f".coverage.{s.python}"
    s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests")


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"], uv_extras=["fastapi"])
def test_fastapi(s: Session):
    coverage_file = f".coverage.{s.python}.fastapi"
    s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests/fastapi")


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"], uv_extras=["numpy"])
def test_numpy(s: Session):
    coverage_file = f".coverage.{s.python}.numpy"
    s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests/test_numpy.py")


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"], uv_extras=["ordered-set"])
def test_ordered_set(s: Session):
    coverage_file = f".coverage.{s.python}.ordered_set"
    s.run(
        "coverage",
        "run",
        "--data-file",
        coverage_file,
        "-m",
        "pytest",
        "tests/implementations/test_ordered_set.py",
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


@session(venv_backend="none")
def typecheck(s: Session):
    s.run("ty", "check", "tests/type_checking")
