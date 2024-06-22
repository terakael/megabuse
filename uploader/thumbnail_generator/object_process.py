import logging
from abc import ABC, abstractmethod
from PIL import Image

logger = logging.getLogger('object_process')

class ObjectProcess(ABC):
    """
    Abstract base class for processing objects, such as images and videos.

    Methods:
        __init__(input_path): Initialize with the path to the input file.
        _fetch_image(): Fetch the image from the input path.
        _pre_process(image): Pre-process the image before generating the thumbnail.
        _post_process(thumb): Post-process the generated thumbnail.
        _generate_thumbnail(image, thumb_size): Generate a thumbnail from the image.
        create_thumbnail(thumb_size): Create a thumbnail for the input file.
    """
    @abstractmethod
    def __init__(self, input_path):
        self.input_path = input_path
    
    def _fetch_image(self):
        return Image.open(self.input_path)
    
    def _pre_process(self, image):
        return image

    def _post_process(self, thumb):
        return thumb

    def _generate_thumbnail(self, image, thumb_size):
        width, height = image.size

        # make it square if it isn't already
        if width != height:
            min_dimension = min(width, height)
            left = (width - min_dimension) // 2
            top = (height - min_dimension) // 2
            right = left + min_dimension
            bottom = top + min_dimension
            image = image.crop((left, top, right, bottom))
        
        # resize the square image to the largest dimension of the thumbnail
        max_thumb_dimension = max(thumb_size)
        image = image.resize((max_thumb_dimension, max_thumb_dimension), Image.LANCZOS)

        # given the shrunken image, crop out the actual thumbnail
        new_width, new_height = thumb_size
        left = (max_thumb_dimension - new_width) // 2
        top = (max_thumb_dimension - new_height) // 2
        right = left + new_width
        bottom = top + new_height
        return image.crop((left, top, right, bottom))

    def create_thumbnail(self, thumb_size):
        image = self._fetch_image()
        image = self._pre_process(image)
        
        thumb = self._generate_thumbnail(image, thumb_size)
        thumb = self._post_process(thumb)

        return thumb