import os

class Config:
    def __init__(self):
        self.output_dir = os.getenv("DOWNLOAD_DIR", "./downloads")
        self.max_image_workers = int(os.getenv("MAX_IMAGE_WORKERS", 5))
        self.max_chapter_workers = int(os.getenv("MAX_CHAPTER_WORKERS", 2))
        self.retry_count = int(os.getenv("RETRY_COUNT", 3))
        self.retry_base_delay = float(os.getenv("RETRY_DELAY", 2))

def get_config():
    return Config()
