from uuid import uuid4
import PIL.Image as Image
import io
import time
from config import load_config
import requests
import urllib.parse

config = load_config()
uuidChars = ("a", "b", "c", "d", "e", "f",
             "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
             "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5",
             "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I",
             "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
             "W", "X", "Y", "Z")

def short_uuid():
    uuid = str(uuid4()).replace('-', '')
    result = ''
    for i in range(0, 8):
        sub = uuid[i * 4: i * 4 + 4]
        x = int(sub, 16)
        result += uuidChars[x % 0x3E]
    return result


def get_filename(ext: str = ""):
    now = time.time()
    filename = time.strftime("%Y%m%d", time.localtime(now))
    filename = filename+"_"+short_uuid()
    if ext.startswith("."):
        filename = filename + ext
    elif ext != "":
        filename = filename + "." + ext
    return filename

def upload(image: Image.Image):
    global config
    headers = {'Authorization': config.gallery.token}

    buff = io.BytesIO()
    image.save(buff, "jpeg")
    buff.seek(0)

    filename = get_filename("jpg")
    files = {
        'result': (filename, buff, "image/jpeg")
    }

    res = requests.post(config.gallery.url, files=files,
                        headers=headers).json()
    if res["code"] == 0:
        return {
            "code": 0,
            "url": urllib.parse.urljoin(config.gallery.externurl, filename)
        }
    else:
        return {
            "code": 1,
            "message": res,
            "url": ""
        }
