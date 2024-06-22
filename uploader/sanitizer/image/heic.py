from image.base import Base
from PIL import Image
import pyheif

class Heic(Base):
    def __init__(self, filepath):
        super().__init__(filepath)
    
    def load_image(self):
        heif_file = pyheif.read(self.filepath)
        return Image.frombytes(
            heif_file.mode, 
            heif_file.size, 
            heif_file.data, 
            "raw", 
            heif_file.mode, 
            heif_file.stride,
        )