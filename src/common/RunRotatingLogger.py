import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

class RunRotatingLogger:
    def __init__(
        self,
        name: str,
        log_file: str,
        level: int = logging.INFO,
        backup_count: int = 5,
        when: str = 'midnight',
        interval: int = 1,
        utc: bool = True
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False

        # Only add handler if it hasn't been added yet
        if not self.logger.handlers:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)  # Ensure log directory exists

            handler = TimedRotatingFileHandler(
                filename=log_file,
                when=when,
                interval=interval,
                backupCount=backup_count,
                encoding='utf-8',
                utc=utc
            )

            # Rotate immediately on startup
            handler.doRollover()

            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)

    def get(self):
        return self.logger
