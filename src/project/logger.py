import logging
import logging.handlers as handlers
import sys
import os
from pathlib import Path

if("LOG_DIR" not in os.environ):
    raise EnvironmentError(f"Missing 'LOG_DIR' in environment variable")
if("LOG_NAME" not in os.environ):
    raise EnvironmentError(f"Missing 'LOG_NAME' in environment variable")
if("LOG_ROTATE_NAME" not in os.environ):
    raise EnvironmentError(f"Missing 'LOG_ROTATE_NAME' in environment variable")

_LOG_DIR = Path(os.environ["LOG_DIR"])
_LOG_PATH = _LOG_DIR.joinpath(os.environ["LOG_NAME"])
_LOG_ROTATE_PATH = _LOG_DIR.joinpath(os.environ["LOG_ROTATE_NAME"])

# log format
formatter = logging.Formatter('%(asctime)s|%(filename)s:%(funcName)s:%(lineno)d|%(levelname)s|%(message)s')
formatter.datefmt = '%d-%m-%Y %H:%M:%S'

# console handler
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(formatter)

# file handler
# fileHandler = logging.FileHandler(filename=file)
# fileHandler.setFormatter(formatter)
# This will rotate log
fileHandler = handlers.RotatingFileHandler(filename=_LOG_ROTATE_PATH, mode='a', maxBytes=10240000, backupCount=10)
fileHandler.setFormatter(formatter)
fileHandler2 = logging.FileHandler(filename=_LOG_PATH, mode='a')
fileHandler2.setFormatter(formatter)


logging.basicConfig(
    level=logging.INFO,
    handlers=[
        fileHandler,
        fileHandler2,
        consoleHandler
    ]
)


# # Configures the root logger, affecting all other loggers
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("app.log"),
#         logging.StreamHandler()
#     ]
# )

# def _create_folder(filename:str):
#     path, name = os.path.split(filename)
#     os.makedirs(name=path, exist_ok=True)

# def init_logger(name:str, filename:str, path:str, level:int=logging.INFO) -> Logger:
#     logger = logging.getLogger(name)
#     logger.setLevel(level)
#     filename = "/".join(filename.split('.'))
#     filename = os.path.join(path,f"{filename}.log")
#     _create_folder(filename=filename)

#     # Handler


#     # Add Handler
#     logger.addHandler(consoleHandler)
#     logger.addHandler(fileHandler)
#     logger.addHandler(fileHandler2)

#     logger.propagate = False
#     return logging.getLogger(name)