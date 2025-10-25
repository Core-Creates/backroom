# noxfile.py
import nox
import os

@nox.session(reuse_venv=True)
def tests(session):
    # Install app deps
    session.install("-r", "requirements.txt")
    # Install test deps
    session.install("pytest")

    #repo_root = str(pathlib.Path(__file__).resolve().parent)
    #env = {"PYTHONPATH": repo_root}  # IMPORTANT: parent of `src/`, i.e., the repo root

    # Run tests with short, quiet output
    session.run("pytest", "-q")

def lint(session):
    session.install("flake8")
    session.run("flake8", "backroom", "tests")