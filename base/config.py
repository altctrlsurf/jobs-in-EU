import logging
import os
from datetime import datetime

def setup_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_filename = datetime.now().strftime('logs/scraper_%Y%m%d_%H%M%S.log')

    # Configure logging format
    log_format = '%(asctime)s - %(filename)s - %(threadName)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

class Output:

    def __init__(self, base_name=None):
        self.base_name = base_name
        if not os.path.exists("output"):
            os.makedirs("output")

        ymd = datetime.now().strftime("%Y%m%d")
        self.output_path = os.path.join("output", ymd)
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

        if self.base_name:
            self.output_path = os.path.join(self.output_path, self.base_name)
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)

    def get_filename(self, filename):
        return os.path.join(self.output_path, filename)