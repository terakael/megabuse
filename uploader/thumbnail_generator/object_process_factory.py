import logging
import magic
from .image_process import ImageProcess
from .video_process import VideoProcess

logger = logging.getLogger('object_process_factory')

class ObjectProcessFactory:
    """
    Factory class for creating appropriate ObjectProcess instances based on file type.

    Methods:
        __init__(): Initialize the factory with MIME type detection.
        create(filepath): Create an ObjectProcess instance based on the file type.
    """
    def __init__(self):
        self.mime = magic.Magic(mime=True)
    
    def create(self, filepath):
        match self.mime.from_file(filepath).split('/')[0]:
            case 'video':
                logger.debug(f'spawning VideoProcess for {filepath}')
                return VideoProcess(filepath)
                
            case 'image':
                logger.debug(f'spawning ImageProcess for {filepath}')
                return ImageProcess(filepath)

            case _:
                logger.warn(f'{filepath} not image or video.')
                return None