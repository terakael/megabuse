import logging
import os
from PIL import Image

logger = logging.getLogger('video_base')

class Base:
    def __init__(self, filepath):
        self.path, self.filename = os.path.split(filepath)

    @property
    def filepath(self):
        return os.path.join(self.path, self.filename)

    def process(self, output_dir):
        image = self.load_image()
        image.save(
            os.path.join(
                output_dir, 
                os.path.splitext(self.filename)[0] + '.jpg'
            ), 
            "JPEG"
        )

        os.remove(self.filepath)
    
    def load_image(self):
        return Image.open(self.filepath)