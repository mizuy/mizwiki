from mizwiki import config
import logging

logging.basicConfig(filename=config.LOG_FILENAME,level=logging.DEBUG)

def log(msg):
    logging.debug(msg)
