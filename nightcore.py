from pydub import AudioSegment
from io import BytesIO
import urllib

def speed_change(url, speed=1.0):
    file = urllib.request.urlopen(url).read()
    sound = AudioSegment.from_file(BytesIO(file))
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
