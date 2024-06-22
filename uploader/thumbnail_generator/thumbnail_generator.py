import os
import logging
from .object_process_factory import ObjectProcessFactory

logger = logging.getLogger('thumbnail_generator')

def generate_thumbnails(
    *, 
    src_dir: str, 
    dest_dir: str, 
    thumb_size: tuple=(96, 128),
    quality=40
) -> None:
    """
    Generate thumbnails for each file in the source directory and save them to the destination directory.

    Args:
    src_dir (str): The directory to scan for files.
    dest_dir (str): The directory where thumbnails will be saved.
    thumb_size (tuple): The size of the thumbnails as a tuple (width, height), default is (96, 128).
    """
    
    factory = ObjectProcessFactory()
    
    for entry in os.scandir(src_dir):
        logger.info(f'processing {entry.path}')
        
        if not entry.is_file():
            logger.debug(f'skipping non-file {entry.path}')
            continue

        process = factory.create(entry.path)
        if not process:
            continue

        thumb = process.create_thumbnail(thumb_size)
        thumb.save(
            f'{dest_dir}/{entry.name}.jpg', 
            format='JPEG', 
            quality=quality, 
            optimize=True
        )
