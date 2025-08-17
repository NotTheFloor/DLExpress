import logging
import sys
from datetime import datetime
from pathlib import Path

class WorkflowDesignerLogger:
    """Centralized logging for the Workflow Designer"""
    
    def __init__(self, name="WorkflowDesigner", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Console handler (default)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def add_file_handler(self, log_file: str, level=logging.INFO):
        """Add a file handler to log to a file"""
        # Create file handler
        file_handler = logging.FileHandler(log_file, mode='w')  # 'w' to overwrite each run
        file_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info(f"File logging enabled: {log_file}")
    
    def set_level(self, level):
        """Set the logging level"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)
        # Also update all handlers
        for handler in self.logger.handlers:
            handler.setLevel(level)
    
    def info(self, message):
        self.logger.info(message)
    
    def warning(self, message):
        self.logger.warning(message)
    
    def error(self, message):
        self.logger.error(message)
    
    def debug(self, message):
        self.logger.debug(message)
    
    def critical(self, message):
        self.logger.critical(message)

# Global logger instance
logger = WorkflowDesignerLogger()

def configure_logging(log_file: str = None, level: str = 'INFO'):
    """
    Configure the global logger with file output and/or debug level
    
    Args:
        log_file: Optional file path to log to. If None, only console logging is used.
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    """
    global logger
    
    # Set the logging level
    logger.set_level(level)
    
    # Add file handler if requested
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add file handler
        logger.add_file_handler(log_file, getattr(logging, level.upper()))
        
        # Generate a timestamped file name if user wants it
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger.info(f"Logging session started at {timestamp}")
        logger.info(f"Command line logging configured: file={log_file}, level={level}")
    else:
        logger.info(f"Console logging configured: level={level}")