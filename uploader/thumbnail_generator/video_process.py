from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont
from .object_process import ObjectProcess

class VideoProcess(ObjectProcess):
    """
    Process class for handling videos, inherits from ObjectProcess.

    Methods:
        __init__(input_path): Initialize with the path to the video file.
        _fetch_image(): Fetch a frame from the video file.
        _post_process(thumb): Add duration text to the generated thumbnail.
    """
    def __init__(self, input_path):
        super().__init__(input_path)
    
    def _fetch_image(self):
        with VideoFileClip(
            self.input_path, 
            audio=False, 
        ) as clip:
            if clip.rotation in [90, 270]:
                # clips in portrait with rotation metadata
                # are rotated to landscape but this causes
                # image distortion.  This fixes it.
                clip = clip.resize(clip.size[::-1])
                clip.rotation = 0

            self.duration = clip.duration
            return Image.fromarray(clip.get_frame(clip.duration * 0.5))
    
    def _post_process(self, thumb):
        text = f'{(int(self.duration) // 60):02}:{(int(self.duration) % 60):02}'
                
        draw = ImageDraw.Draw(thumb)
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 25)

        text_width, text_height = draw.textsize(text, font=font)
        thumb_width, thumb_height = thumb.size
        text_pos = ((thumb_width - text_width) // 2, (thumb_height - text_height) - 5)
        
        draw.text(text_pos, text, font=font, fill="white", stroke_fill="black", stroke_width=3)

        return thumb