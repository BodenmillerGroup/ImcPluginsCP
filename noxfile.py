import nox

nox.options.sessions = ["tests"]


@nox.session(python=["3.8"])
def tests(session):
    args = session.posargs or []
    session.run("poetry", "install", external=True)
    session.run("poetry", "run", "pytest", "--cov")


locations = "plugins", "noxfile.py", "tests"


@nox.session(python=["3.8"])
def lint(session):
    args = session.posargs or locations
    session.install("flake8", "flake8-black", "flake8-bugbear", "flake8-import-order")
    session.run("flake8", *args)


@nox.session(python="3.8")
def black(session):
    args = session.posargs or locations
    session.install("black")
    session.run("black", *args)


@nox.session(python=["3.8"])
def mypy(session):
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)
