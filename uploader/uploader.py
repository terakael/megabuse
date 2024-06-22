"""
process:
- unsanitized files are dropped into /unprocessed (by user)
- sanitizer sanitizes to /sanitized (jpg, webm)
- thumbnails created into /thumbnails
- previews created into /previews
- images/thumbnails/previews encrypted and round-robinned from /sanitized into server directories, metadata written
- videos chunked into /video_chunks
- video_000.webm copied into /previews
- /video_chunks/thumbnails encrypted and round-robinned from /video_chunks into server directories; metadata written
- database encrypted and copied into all server directories
- server directories uploaded to their respective server
- /thumbnails moved to ui static/thumnails folder
- /previews moved to ui static/previews folder
"""

import os
import sys
import logging
import sqlite3
import time
import subprocess
import shutil
import base64
import glob
import random
import re
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image

from thumbnail_generator import generate_thumbnails
# from sanitizer import sanitize
from common.encrypt import Encrypter

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger('object_process_factory')
load_dotenv()

def unix_timestamp(filename):
    if match := re.search(r'\d{8}_\d{6}', filename):
        try:
            dt = datetime.strptime(match.group(), '%Y%m%d_%H%M%S')
            return int(dt.timestamp())
        except:
            pass # fall through to main return
    return int(time.time())

mega_root = os.getenv('mega_root')
def path(*subdirecties):
    return os.path.join(mega_root, *subdirecties)

# load available storage servers from db
db_file = path('database.db')
with sqlite3.connect(db_file) as conn:
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('select * from servers')
    servers = cursor.fetchall()

# create work dir with children named after storage servers
for server in servers:
    os.makedirs(path(server['email']), exist_ok=True)
os.makedirs(path('thumbnails'), exist_ok=True)
os.makedirs(path('video_chunks'), exist_ok=True)
os.makedirs(path('previews'), exist_ok=True)

src_dir = path('sanitized')





# users can dump any kind of image/video file here,
# and we'll sanitize them into jpg/webm files for further processing.
logger.info('sanitizing data...')
# sanitize(path('unprocessed'), src_dir)




# now we have sanitized files, we can generate thumbnails from them.
# this step needs to be done here because we'll be breaking up
# the videos into chunks, and we only want one thumbnail per video.
logger.info('generating thumbnails...')
generate_thumbnails(
    src_dir=src_dir, 
    dest_dir=path('thumbnails'),
    thumb_size=(128*2, 96*2)
)


# all images have a corresponding preview.
# we cache this alongisde the initial video chunk for each video.
logger.info('generating previews...')
for filepath in glob.glob(path('sanitized', '*.jpg')):
    img = Image.open(filepath)
    max_width = 1080
    max_height = 1920

    if img.width > max_width or img.height > max_height:
        if img.width > img.height:
            new_width = max_width
            new_height = int((max_width / img.width) * img.height)
        else:
            new_height = max_height
            new_width = int((max_height / img.height) * img.width)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        
    filename = os.path.basename(filepath)
    img.save(path('previews', filename), 'JPEG', quality=20, optimize=True)



# encrypt and move images into work dir children, round robin style, updatin db
encrypter = Encrypter(
    key=base64.b64decode(os.getenv('key')), 
    iv=base64.b64decode(os.getenv('iv'))
)

def encrypt_and_move(src_glob):
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        counter = 0
        for filepath in glob.glob(src_glob):
            filename = os.path.basename(filepath)

            dek = Encrypter.generate_iv()
            encrypted_dek = encrypter.encrypt(dek)

            email = servers[counter % len(servers)]['email']
            encrypter.encrypt_file(
                src_file=filepath,
                dest_file=path(email, encrypter.hash(filename, iv=dek)),
                iv=dek
            )

            # videos are chunked, and there's only one thumbnail for the whole set.
            if filename.endswith('.jpg') or filename.endswith('_0000.webm'):
                thumb_filename = f"{filename.replace('_0000.webm', '.webm')}.jpg"
                thumb_filepath = os.path.join(path('thumbnails', thumb_filename))

                # no need to store the thumbnail entry in the metastore.
                # we know its filename and which server it's on based on the main file.
                encrypter.encrypt_file(
                    src_file=thumb_filepath,
                    dest_file=path(email, encrypter.hash(thumb_filename, iv=dek)),
                    iv=dek
                )
            
            if filename.endswith('.jpg'):
                # images also have their corresponding preview.
                # we give it a different hash than the original image
                # by appending ".preview" on it.
                encrypter.encrypt_file(
                    src_file=path('previews', filename),
                    dest_file=path(email, encrypter.hash(f'{filename}.preview', iv=dek)),
                    iv=dek
                )

            cursor.execute('insert into files values (?, ?, ?, ?)', [
                filename,
                unix_timestamp(filename),
                email,
                encrypted_dek
            ])

            counter += 1
        conn.commit()

# enrypt and move the images first - videos need further processing
logger.info('encrypting images...')
encrypt_and_move(os.path.join(src_dir, '*.jpg'))



# chunk the videos
logger.info('chunking videos...')
for filepath in glob.glob(os.path.join(src_dir, '*.webm')):
    filename = os.path.basename(filepath)
    with open(filepath, 'rb') as infile:
        chunk_number = 0
        while True:
            # randomize filesize so mega can't tell what it is.
            # if they were all 1mb exactly then it's kinda obvious
            chunk = infile.read(random.randint(700 * 1024, 2 * 1024 * 1024))
            if not chunk:
                break

            with open(path('video_chunks', filename.replace('.webm', f'_{chunk_number:04d}.webm')), 'wb') as outfile:
                outfile.write(chunk)

            chunk_number += 1


# keep the first chunk of each video for quick serving
logger.info('copying preview video chunks...')
for filepath in glob.glob(os.path.join(path('video_chunks', '*_0000.webm'))):
    shutil.copyfile(filepath, path('previews', os.path.basename(filepath)))

# now encrypt and move all the chunks to their upload directories
logger.info('encrypting video chunks...')
encrypt_and_move(os.path.join(path('video_chunks'), '*.webm'))

def upload_to_server(server):
    dek = encrypter.decrypt(server['dek'])

    command = [
        'megatools',
        'copy',
        '--username', server['email'],
        '--password', encrypter.decrypt(server['mega_pw'], iv=dek).decode('utf-8'),
        '--local', path(server['email']),
        '--remote', '/Root'
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    while True:
        line = process.stdout.readline()
        if not line:
            break
        logger.info(line)

# back up the db file in each of the remote storages
for server in servers:
    encrypter.encrypt_file(
        src_file=db_file,
        dest_file=path(server['email'], encrypter.hash(server['email']))
    )

    upload_to_server(server)

    logger.info('removing local directory ' + path(server['email']))
    shutil.rmtree(path(server['email']))

# move the thumbnails and previews into their respective ui static directory
for directory in ['thumbnails', 'previews']:
    for filepath in glob.glob(path(directory, '*.*')):
        shutil.move(filepath, f'/home/dan/storage/docker/megabuse/ui/static/{directory}')