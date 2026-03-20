import sys
import os
import tempfile
from PIL import Image
import warnings

def _get_data(img):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return list(img.getdata())

def run():
    secret_message = "A" * 4000
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img = Image.new('RGB', (100, 100), color='white')
    img.save(path)

    img = Image.open(path)
    img = img.convert("RGB")

    binary_message = ''.join(format(ord(char), '08b') for char in secret_message)
    binary_message += '1111111111111110'

    data = _get_data(img)

    print(f"data len: {len(data)}")
    print(f"binary_message len: {len(binary_message)}")
    if len(binary_message) > len(data) * 3:
        print("Message is too large to fit in this image.")
    else:
        print("Fits fine.")

run()
