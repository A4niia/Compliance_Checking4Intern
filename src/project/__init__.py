from dotenv import load_dotenv
from pathlib import Path
import sys

_ENVFILE:Path = Path("local.env")
if(_ENVFILE.exists() == False):
    print("[Warning] Missing `local.env`. We assume all variables is in `os.environ`", file=sys.stderr)
load_dotenv(dotenv_path=_ENVFILE)


# We do this to load the logger (which will config the logger for this module)
import project.logger # type: ignore
from typer import Typer
from project.cli import cli as main_cli# type: ignore
from project.processor.subtraction import cli as subtract_cli# type: ignore


# This is how you do logging
import logging
logging.debug("App start")

# This is how can we structure the cli
cli = Typer()
cli.add_typer(main_cli)
cli.add_typer(subtract_cli)


