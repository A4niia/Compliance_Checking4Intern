"""
This module shows an example of developing a cli with `typer`
Learn more [here](https://typer.tiangolo.com/tutorial/printing/#rich-markup)
"""

import typer
from rich import print
from typing import Annotated

import os
import logging

_PROJECT_NAME = os.environ["PROJECT_NAME"]

# adding command
from project.processor.subtraction import cli as subtract_cli
from project.web import cli as web_cli

cli = typer.Typer()
cli.add_typer(subtract_cli)
cli.add_typer(web_cli, name="web", help="The cli for web module")

@cli.command()
def command_1():
    """
    This is the default command. You can find this command in `src/python_project_stater/cli.py`.
    """
    logging.debug("Calling `command_1`")
    print(f"Welcome to {_PROJECT_NAME}")


@cli.command()
def addition(a:Annotated[int, typer.Argument(help="First number argument")], 
        b:Annotated[int, typer.Argument(help="Second number argument")]):
    """
    This is the another default command.
    It will perform an addition between `a` and `b`.
    """
    logging.debug("Calling `addition`")
    print(f"The calculation is {a+b}.")