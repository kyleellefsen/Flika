from logging import *
import os, sys

def get_log_file():
    LOG_DIR = os.path.join(os.path.expanduser("~"), '.FLIKA', 'log')
    MAX_LOG_IDX = 99
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    existing_files = os.listdir(LOG_DIR)
    if 'FLIKALOG.log' in existing_files: # This was the name of the log file before version 0.2.23
        try:
            os.remove(os.path.join(LOG_DIR, 'FLIKALOG.log'))
        except:
            existing_files.remove('FLIKALOG.log')
        existing_files = os.listdir(LOG_DIR)

    try:
        existing_idxs = [int(f.split('.')[0]) for f in existing_files]
    except ValueError:
        print("There is an error with your log folder. Delete all files inside ~/.FLIKA/log/ and restart flika.")
    log_idx = 0
    while log_idx in existing_idxs:
        log_idx += 1
    log_idx = log_idx % MAX_LOG_IDX
    idx_to_delete = (int(log_idx) + 1) % MAX_LOG_IDX
    LOG_FILE_TO_DELETE = os.path.join(LOG_DIR, '{0:0>3}.log'.format(idx_to_delete))
    if os.path.exists(LOG_FILE_TO_DELETE):
        try:
            os.remove(LOG_FILE_TO_DELETE)
        except Exception as e:
            print(e)
    LOG_FILE = os.path.join(LOG_DIR, '{0:0>3}.log'.format(log_idx))
    return LOG_FILE

LOG_FILE = get_log_file()
FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
basicConfig(filename=LOG_FILE, format=FORMAT)
logger = getLogger("flika")
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
formatter = Formatter(FORMAT)
handler.setFormatter(formatter)
logger.addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
sys.excepthook = handle_exception