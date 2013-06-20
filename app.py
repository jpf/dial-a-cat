from PIL import Image
from random import choice
import os

from flask import Flask
from flask import Response
from flask import url_for
from twilio import twiml

from catapi import CatAPIPicture
from filegenerator import FileGenerator
from martinstreaming import MartinM2Generator
from martinstreaming import MartinM2GeneratorWorker

app = Flask(__name__)


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
    rv.headers['Content-Length'] = 5661190
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
    rv.headers['Content-Length'] = 5661190
    return rv

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
