from PIL import Image
from StringIO import StringIO
from itertools import izip_longest
from random import choice
from wave import Wave_write
import os
import re
import requests
import struct
import threading

from flask import Flask
from flask import Response
from flask import url_for
from twilio import twiml

from color import MartinM2
from filegenerator import FileGenerator

app = Flask(__name__)


class WaveWriteNoSeek(Wave_write):
    def _patchheader(self):
        return None


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)


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


class CatAPIPicture:
    def __init__(self, id=False):
        self.image = None
        if id:
            self.id = id
            self._image_from_id()
        else:
            self._random_image()

    def _random_image(self):
        url = 'http://thecatapi.com/api/images/get?format=xml&type=jpg'
        return self._fetch_url(url)

    def _image_from_id(self):
        url = 'http://thecatapi.com/api/images/get?format=xml&id=%s' % self.id
        return self._fetch_url(url)

    def _fetch_url(self, url):
        r = requests.get(url)
        match = re.search(r"<id>([^<]+)</id>", r.content)
        self.id = match.group(1)
        match = re.search(r"<url>([^<]+)</url>", r.content)
        self.url = match.group(1)
        match = re.search(r"<source_url>([^<]+)</source_url>", r.content)
        self.source_url = match.group(1)

    def image_get(self):
        r = requests.get(self.url)
        self.image = Image.open(StringIO(r.content))

    def image_scale_to(self, target_tuple):
        target = Size(target_tuple)
        actual = Size(self.image.size)
        changed = Size()
        scale = float(target.width) / float(actual.width)
        changed.width = int(round(actual.width * scale))
        changed.height = int(round(actual.height * scale))
        want = changed.as_tuple()
        resized = self.image.resize(want)
        if changed.height < target.height:
            # add blackness to the bottom
            black = Image.new('RGB', (target.width, target.height))
            black.paste(resized, (0, 0))
            resized = black
        elif changed.height > target.height:
            # crop out the bottom
            resized = resized.crop((0, 0, target.width, target.height))
        self.image = resized


class Size:
    def __init__(self, input=None):
        if input is None:
            input = (0, 0)
        (self.width, self.height) = input

    def as_tuple(self):
        return (self.width, self.height)


@app.route('/')
def main():
    return 'hi'


@app.route('/voice', methods=['GET', 'POST'])
def voice():
    r = twiml.Response()
    r.say("Welcome to dial a cat.")
    r.say("S S T V Transmission in Martin M Two format starting shortly.")
    r.say("Standby.")
    r.redirect(url_for('random_cat', _external=True))
    return str(r)


@app.route('/voice/random-api-cat', methods=['GET', 'POST'])
def random_api_cat():
    cat = CatAPIPicture()
    sstv_wav_url = url_for('cat_sstv_wav',
                           id=cat.id,
                           _external=True)
    r = twiml.Response()
    r.say("Playing S S T V file now")
    with r.gather() as g:
        g.play(sstv_wav_url)
    return str(r)


@app.route('/voice/random-cat', methods=['GET', 'POST'])
def random_cat():
    f = open('image-list.txt')
    images = [i.strip() for i in f.readlines()]
    wav = 'https://s3.amazonaws.com/jf-sstv-cats/%s' % choice(images)
    r = twiml.Response()
    with r.gather() as g:
        g.play(wav)
    r.redirect(url_for('random_cat', _external=True))
    return str(r)


@app.route('/cat-api/v1/sstv-<id>.wav')
def cat_sstv_wav(id):
    # MartinM2
    target = (160, 256)
    cat = CatAPIPicture(id=id)
    cat.image_get()
    cat.image_scale_to(target)

    generator = FileGenerator()
    slowscan = MartinM2Generator(cat.image, 48000, 16)
    MartinM2GeneratorWorker(slowscan, generator).start()

    rv = Response(generator.read_generator(), mimetype='audio/wav')
    rv.headers['Content-Length'] = 5568508
    rv.headers['Cache-Timeout'] = 14400  # 4 hours
    # rv.headers['Cache-Timeout'] = 604800 # 1 week
    return rv


@app.route('/test.wav')
def image_test():
    image = Image.open('pySSTV/tests/assets/160x256_test_pattern.png')

    generator = FileGenerator()
    slowscan = MartinM2Generator(image, 48000, 16)
    MartinM2GeneratorWorker(slowscan, generator).start()

    rv = Response(generator.read_generator(), mimetype='audio/wav')
    rv.headers['Content-Length'] = 5568508
    return rv

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
