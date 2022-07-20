from loguru import logger
import sys


def info(message: str) -> str:
    logger.configure(
        handlers=[
        dict(sink=sys.stderr, format="<green>{message}</green>", colorize=True,)
    ],
    )
    return logger.info(message) 

def error(message: str) -> str:
    logger.configure(
        handlers=[
        dict(sink=sys.stderr, format="[{time:YYYY.MM.DD} {time:HH:mm:ss}] <red>{level}</red>: {message}", colorize=True)
    ],
    )
    return logger.error(message) 
