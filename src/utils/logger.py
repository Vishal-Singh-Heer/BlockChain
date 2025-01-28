import logging
import os
import sys
import json
from datetime import datetime
from typing import Optional

def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Creates and returns a logger instance with the specified name and configuration.
    
    Args:
        name: The name of the logger (typically __name__)
        log_level: Optional logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if the logger hasn't been configured yet
    if not logger.handlers:
        # Set log level
        level = getattr(logging, (log_level or 'INFO').upper())
        logger.setLevel(level)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )

        # Create file handler
        log_file = os.path.join(
            logs_dir, 
            f'nexuschain_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # Load any custom logging configuration
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'logging_config.json'
        )
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                # Apply custom configuration
                if 'log_level' in config:
                    logger.setLevel(getattr(logging, config['log_level'].upper()))
                if 'format' in config:
                    custom_formatter = logging.Formatter(config['format'])
                    for handler in logger.handlers:
                        handler.setFormatter(custom_formatter)
                        
            except Exception as e:
                logger.warning(f"Failed to load custom logging configuration: {str(e)}")

    return logger

def setup_global_logger(log_level: str = 'INFO') -> None:
    """
    Sets up global logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = get_logger('nexuschain', log_level)
    logging.root = root_logger

class LoggerWrapper:
    """
    Wrapper class to provide context-based logging.
    """
    def __init__(self, name: str, context: Optional[dict] = None):
        self.logger = get_logger(name)
        self.context = context or {}

    def _format_message(self, message: str) -> str:
        if self.context:
            context_str = ' '.join(f'{k}={v}' for k, v in self.context.items())
            return f"{message} [{context_str}]"
        return message

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_message(message), **kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_message(message), **kwargs)

    def add_context(self, **kwargs):
        self.context.update(kwargs)

    def remove_context(self, *keys):
        for key in keys:
            self.context.pop(key, None)

# Example logging configuration file (config/logging_config.json):
"""
{
    "log_level": "INFO",
    "format": "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    "file_logging": {
        "enabled": true,
        "path": "logs/nexuschain.log",
        "max_size": 10485760,
        "backup_count": 5
    },
    "console_logging": {
        "enabled": true,
        "format": "%(levelname)s - %(message)s"
    }
}
"""