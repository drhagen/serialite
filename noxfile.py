import shutil

from nox import Session, options, parametrize
from nox_uv import session

options.default_venv_backend = "uv"
options.sessions = ["test", "test_fastapi", "test_numpy", "test_ordered_set", "coverage", "lint"]


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"])
def test(s: Session):
    coverage_file = f".coverage.{s.python}"
    s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests")


@session(python=["3.12", "3.13", "3.14"], uv_groups=["test"], uv_extras=["fastapi"])
@parametrize("resolution", ["locked", "lowest-direct"])
def test_fastapi(s: Session, resolution: str):
    # Back up and restore uv.lock because uv sync --resolution mutates it
    # (https://github.com/dantebben/nox-uv/issues/73).
    shutil.copy2("uv.lock", "uv.lock.bak")

    try:
        if resolution == "lowest-direct":
            s.run(
                "uv",
                "sync",
                "--no-default-groups",
                "--group=test",
                "--extra=fastapi",
                "--resolution=lowest-direct",
                external=True,
            )

        coverage_file = f".coverage.{s.python}.fastapi.{resolution}"
        s.run("coverage", "run", "--data-file", coverage_file, "-m", "pytest", "tests/fastapi")

    finally:
        shutil.move("uv.lock.bak", "uv.lock")


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
