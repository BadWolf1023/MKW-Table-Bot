import sys
import logging

custom_logging_str = logging.Formatter("[%(asctime)s.%(msecs)03d] %(levelname)s [%(thread)d] - %(message)s")

CONSOLE_LOGGING_LEVEL = logging.INFO
LOG_FILE_LOGGING_LEVEL = logging.INFO

def get_logger():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(LOG_FILE_LOGGING_LEVEL)

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler('logfile.log', encoding='utf-8', )
    file_handler.setLevel(LOG_FILE_LOGGING_LEVEL)
    file_handler.setFormatter(custom_logging_str)

    # Create a stream handler to print logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(CONSOLE_LOGGING_LEVEL)  # You can set the desired log level for console output
    console_handler.setFormatter(custom_logging_str)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
