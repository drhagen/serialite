import nox_poetry


@nox_poetry.session(python=["3.10", "3.11"])
def test(session: nox_poetry.Session):
    session.install(".", "pytest", "pytest-cov")
    session.env["COVERAGE_FILE"] = f".coverage.{session.python}"
    session.run("python", "-m", "pytest", "--cov", "serialite")


@nox_poetry.session(python=["3.10", "3.11"])
def test_fastapi(session: nox_poetry.Session):
    session.install(".[fastapi]", "pytest", "pytest-cov", "httpx")
    session.env["COVERAGE_FILE"] = f".coverage.fastapi.{session.python}"
    session.run("python", "-m", "pytest", "--cov", "serialite", "tests/fastapi")


@nox_poetry.session(python=["3.10", "3.11"])
def test_numpy(session: nox_poetry.Session):
    session.install(".[numpy]", "pytest", "pytest-cov")
    session.env["COVERAGE_FILE"] = f".coverage.numpy.{session.python}"
    session.run("python", "-m", "pytest", "--cov", "serialite", "tests/test_numpy.py")


@nox_poetry.session(venv_backend="none")
def coverage(session: nox_poetry.Session):
    session.run("coverage", "combine")
    session.run("coverage", "html")
    session.run("coverage", "xml")


@nox_poetry.session(venv_backend="none")
def black(session: nox_poetry.Session):
    session.run("black", "--check", ".")


@nox_poetry.session(venv_backend="none")
def isort(session: nox_poetry.Session):
    session.run("isort", "--check", ".")


@nox_poetry.session(venv_backend="none")
def flake8(session: nox_poetry.Session):
    session.run("pflake8", "src", "tests")
