from .object_process import ObjectProcess

class ImageProcess(ObjectProcess):
    """
    Process class for handling images, inherits from ObjectProcess.

    Methods:
        __init__(input_path): Initialize with the path to the image file.
    """
    def __init__(self, input_path):
        super().__init__(input_path)