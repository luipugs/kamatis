import logging
import os
import sys


def makedirs(path):
    isdir = True
    exc_info = None

    try:
        os.makedirs(path)
    except OSError as err:
        if err.errno == 17:  # Path already exists.
            if not os.path.isdir(path):
                message = '{} already exists and is not a dir.'.format(path)
                logging.warning(message)
                isdir = False
        else:
            exc_info = sys.exc_info()
            isdir = False
    except:
        exc_info = sys.exc_info()
        isdir = False

    if exc_info is not None:
        logging.warning('Cannot create {}.'.format(path), exc_info=exc_info)

    return isdir
