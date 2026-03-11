import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Define log directory and file
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
# Example path: d:\HeapTrace\Git-Repos\Proposal-Automation-System\backend\logs

def setup_logging():
    """Sets up robust logging with console and file output."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate a timestamp for the log file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"app_{timestamp}.log")

    # Format for logs
    log_format = logging.Formatter(
        "[%(asctime)s] - [%(levelname)s] - [%(name)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Prevent duplicating handlers
    if not logger.handlers:
        # File handler (10MB max size, keep 5 backups)
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(log_format)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_format)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Convenience initialization when imported
logger = setup_logging()
