from color import MartinM2
from itertools import izip_longest
from wave import Wave_write
import struct
import threading


class WaveWriteNoSeek(Wave_write):
    def _patchheader(self):
        return None


def grouper(iterable, n):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=None, *args)


class MartinM2Generator(MartinM2):
    def write_wav_generator(self, filename):
        """write image to a FileGenerator that will be served by Flask"""
        wav = WaveWriteNoSeek(filename)
        wav.setnchannels(1)
        wav.setsampwidth(self.bits // 8)
        wav.setframerate(self.samples_per_sec)
        #wav.setnframes(5529608)  # Martin M1
        wav.setnframes(2830573)  # Martin M2
        fmt = '<' + self.BITS_TO_STRUCT[self.bits]

        def not_none(thing):
            """remove the 'None' values added by grouper()"""
            return thing is not None

        # arbitrary, but reasonable seeming default
        group_size = self.samples_per_sec
        for sample in grouper(self.gen_samples(), group_size):
            samples = (struct.pack(fmt, b) for b in sample if not_none(b))
            data = ''.join(samples)
            wav.writeframes(data)
        wav.close()


class MartinM2GeneratorWorker(threading.Thread):
    def __init__(self, wav, generator):
        self.wav = wav
        self.generator = generator
        threading.Thread.__init__(self)

    def run(self):
        self.wav.write_wav_generator(self.generator)
