import logging
import sys
from typing import Optional
from pathlib import Path

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize the logger with both file and console handlers"""
        self.logger = logging.getLogger('workday_app')
        self.logger.setLevel(logging.INFO)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # File handler
        log_file = Path('logs/workday_app.log')
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def error(self, message: str, exc_info: Optional[Exception] = None):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)