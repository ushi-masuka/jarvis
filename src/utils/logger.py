"""
Configures and provides a standardized logger for the application.

This module centralizes logging configuration, allowing for consistent log formatting
and handling across all components. It supports file-based logging, console output,
and configurable log levels.
"""

import logging
import os
from datetime import datetime

def setup_logger():
    """
    Initializes and configures a logger instance.

    This function sets up a logger with specified handlers for console and file output.
    It uses the standard library for formatted console logging and standard file handlers
    for persistent logs.

    Args:
        None

    Returns:
        logging.Logger: The configured logger instance.
    """
    # Create a logger
    logger = logging.getLogger("JarvisLogger")
    logger.setLevel(logging.INFO)  # Default log level is INFO

    # Avoid duplicate logging if already configured
    if not logger.handlers:
        # Create a file handler to log to a file
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"jarvis_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # Create a console handler to log to the console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Define log format
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Apply formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    # Example usage for testing
    logger = setup_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")