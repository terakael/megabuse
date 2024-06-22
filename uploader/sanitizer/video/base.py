import logging
import subprocess
import os

logger = logging.getLogger('video_base')

class Base:
    def __init__(self, filepath):
        self.path, self.filename = os.path.split(filepath)

    def process(self, output_dir):
        with subprocess.Popen([
            'ffmpeg',
            '-i', os.path.join(self.path, self.filename),
            '-c:v', "libvpx-vp9",
            '-crf', '30',
            '-b:v', '0',
            os.path.join(output_dir, '.'.join(self.filename.split('.')[:-1] + ['webm']))
        ]) as process:
            process.wait()
        
        os.remove(os.path.join(self.path, self.filename))