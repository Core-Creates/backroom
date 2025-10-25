# noxfile.py
import nox

@nox.session(reuse_venv=True)
def tests(session):
    # Install app deps
    session.install("-r", "requirements.txt")
    # Install test deps
    session.install("pytest")
    # Run tests with short, quiet output
    session.run("pytest", "-q")
def lint(session):
    session.install("flake8")
    session.run("flake8", "backroom", "tests")