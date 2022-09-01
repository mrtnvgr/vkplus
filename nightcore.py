from pydub import AudioSegment
from io import BytesIO
import urllib

def speed_change(url, speed=1.0):
    file = urllib.request.urlopen(url).read()
    sound = AudioSegment.from_file(BytesIO(file))
    sound2 = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    sound2 = sound2.set_frame_rate(sound.frame_rate)
    buf = BytesIO()
    sound2.export(buf)
    return buf.getvalue()
