from typing import Annotated
import typer
from typer import Typer
import logging

cli = Typer()
@cli.command()
def subtraction(a:Annotated[int, typer.Argument(help="First number argument")], 
        b:Annotated[int, typer.Argument(help="Second number argument")]) -> int:
    """
    This is the another default command.
    It will perform a subtraction between `a` and `b`.
    """
    logging.debug("Calling `subtraction`")
    answer:int = a - b
    print(f"The calculation is {answer}.")
    return answer
