from PIL import Image
from random import choice
import os

from flask import Flask
from flask import Response
from flask import redirect
from flask import request
from flask import url_for
from twilio import twiml

from catapi import CatAPIPicture
from filegenerator import FileGenerator
from martinstreaming import MartinM2Generator
from martinstreaming import MartinM2GeneratorWorker

app = Flask(__name__)


@app.route('/')
def main():
    return 'Hi'


@app.route('/voice/handle-gather', methods=['POST'])
def voice_handle_gather():
    digit = request.form['Digits']
    if digit == '0':
        return redirect(url_for('voice_help', _external=True))
    elif digit == '1':
        return redirect(url_for('easter_egg', id='1', _external=True))
    elif digit == '2':
        return redirect(url_for('voice_prerendered_cat', _external=True))
    elif digit == '4':
        return redirect(url_for('easter_egg', id='2', _external=True))
    elif digit == '7':
        return redirect(url_for('easter_egg', id='3', _external=True))
    elif digit == '8':
        return redirect(url_for('voice_live_rendered_cat', _external=True))
    else:
        return redirect(url_for('voice_instructions', _external=True))


@app.route('/voice', methods=['GET', 'POST'])
def voice_main():
    r = twiml.Response()
    r.say("Welcome to dial a cat.")
    r.redirect(url_for('voice_instructions', _external=True))
    return str(r)


def get_gather_args():
    return {'action': url_for('voice_handle_gather', _external=True),
            'numDigits': 1,
            'timeout': 1}


@app.route('/voice/instructions', methods=['GET', 'POST'])
def voice_instructions():
    gather_args = get_gather_args()
    r = twiml.Response()
    with r.gather(**gather_args) as g:
        g.say(("An S S T V Transmission "
               "in the Martin M Two format will be starting shortly."))
        g.pause()
        g.say("For help press 0")
        g.pause()
        g.say("Stand by for transmission.")
    r.redirect(url_for('voice_prerendered_cat', _external=True))
    return str(r)


@app.route('/voice/help', methods=['GET', 'POST'])
def voice_help():
    gather_args = get_gather_args()
    r = twiml.Response()
    with r.gather(**gather_args) as g:
        g.say("At any time during this call you may:")
        g.say("Press 2 for a pre rendered cat.")
        g.say("or.")
        g.say("Press 8 for a live rendered cat.")
        g.say("or.")
        g.say("Press the pound sign to skip transmission.")
        g.say("or.")
        g.say("Press 0 for help.")
        g.say("What happens when you press 7?")
        g.say("There is only one way to find out.")
    r.redirect(url_for('voice_instructions', _external=True))
    return str(r)


@app.route('/voice/random-prerendered-cat', methods=['GET', 'POST'])
def voice_prerendered_cat():
    f = open('image-list.txt')
    images = [i.strip() for i in f.readlines()]
    wav = 'https://s3.amazonaws.com/jf-sstv-cats/%s' % choice(images)

    gather_args = get_gather_args()
    r = twiml.Response()
    with r.gather(**gather_args) as g:
        g.play(wav)
        g.say("Stand by for transmission")
    r.redirect(url_for('voice_prerendered_cat', _external=True))
    return str(r)


@app.route('/voice/random-api-cat', methods=['GET', 'POST'])
def voice_live_rendered_cat():
    cat = CatAPIPicture()
    sstv_wav_url = url_for('cat_sstv_wav',
                           id=cat.id,
                           _external=True)

    gather_args = get_gather_args()
    r = twiml.Response()
    r.say("Rendering a random cat image now.")
    r.say("This will take up to thirty seconds.")
    r.say("Please stand by for transmission.")
    with r.gather(**gather_args) as g:
        g.play(sstv_wav_url)
    r.redirect(url_for('voice_live_rendered_cat', _external=True))
    return str(r)


def live_martin_m2_renderer(image):
    generator = FileGenerator()
    slowscan = MartinM2Generator(image, 48000, 16)

    MartinM2GeneratorWorker(slowscan, generator).start()

    rv = Response(generator.read_generator(), mimetype='audio/wav')
    rv.headers['Content-Length'] = 5661190
    return rv


@app.route('/cat-api/v1/sstv-<id>.wav')
def cat_sstv_wav(id):
    cat = CatAPIPicture(id=id)
    cat.image_get()
    cat.image_scale_to_martin_m2()
    rv = live_martin_m2_renderer(cat.image)
    timeout = 14400  # 4 hours
    # timeout = 604800 # 1 week
    rv.headers['Cache-Timeout'] = timeout
    return rv


@app.route('/test.wav')
def image_test():
    image = Image.open('pySSTV/tests/assets/160x256_test_pattern.png')
    return live_martin_m2_renderer(image)


@app.route('/easter-egg-<id>.wav')
def easter_egg(id):
    filename = "easter-egg-%s.wav" % str(id)
    wav = 'https://s3.amazonaws.com/jf-sstv-cats/%s' % filename
    gather_args = get_gather_args()
    r = twiml.Response()
    with r.gather(**gather_args) as g:
        g.play(wav)
    r.redirect(url_for('voice_instructions', _external=True))
    return str(r)

if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)
