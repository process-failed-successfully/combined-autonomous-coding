import os, time, struct
from datetime import datetime, timezone

KSUID_EPOCH = 1400000000
BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def base62_encode(num: int, min_len: int = 27) -> str:
    if num == 0:
        return BASE62_ALPHABET[0] * min_len
    res = []
    while num > 0:
        num, rem = divmod(num, 62)
        res.append(BASE62_ALPHABET[rem])
    while len(res) < min_len:
        res.append(BASE62_ALPHABET[0])
    return ''.join(reversed(res))

def base62_decode(s: str) -> int:
    num = 0
    for char in s:
        num = num * 62 + BASE62_ALPHABET.index(char)
    return num

timestamp = int(time.time()) - KSUID_EPOCH
payload = os.urandom(16)
packed = struct.pack(">I", timestamp) + payload
num = int.from_bytes(packed, byteorder="big")
k = base62_encode(num, 27)
print("KSUID:", k)
print("Length:", len(k))

num2 = base62_decode(k)
packed2 = num2.to_bytes(20, byteorder="big")
ts = struct.unpack(">I", packed2[:4])[0]
print("Timestamp:", ts)
print("Original TS:", timestamp)
print("Payload hex:", packed2[4:].hex())
print("Original payload hex:", payload.hex())
