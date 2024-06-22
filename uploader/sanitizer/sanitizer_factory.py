import logging
import magic
from video.base import Base as VideoBase
from image.heic import Heic as ImageHeic
from image.base import Base as ImageBase

logger = logging.getLogger('sanitizer_factory')

class SanitizerFactory:
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def create(self, filepath):
        mimetype = self.mime.from_file(filepath)
        _type, _subtype = mimetype.split('/')
        match _type:
            case 'video':
                return VideoBase(filepath)
            
            case 'image':
                match _subtype:
                    case 'heic':
                        return ImageHeic(filepath)
                    case _:
                        return ImageBase(filepath)

            case _:
                logger.warn(f'{filepath} not image or video.')
                return None