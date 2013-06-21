import unittest
import app as flask_app


class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        self.app = flask_app.app.test_client()

    def tearDown(self):
        pass

    def test_has_default_route(self):
        path = "/"
        rv = self.app.get(path)
        self.assertEquals("200 OK", rv.status)
        self.assertIn("Hi", rv.data)

    def test_handle_gather(self):
        path = "/voice/handle-gather"

        # help
        msg = dict(Digits='0', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertHasGather(rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('instructions</Redirect>', rv.data)

        # prerendered cats
        msg = dict(Digits='2', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertHasGather(rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('<Play>', rv.data)
        self.assertIn('</Play>', rv.data)
        self.assertIn('prerendered-cat</Redirect>', rv.data)

        # live rendered cats
        msg = dict(Digits='8', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertHasGather(rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('<Play>', rv.data)
        self.assertIn('.wav</Play>', rv.data)
        self.assertIn('api-cat</Redirect>', rv.data)

        # easter egg #1
        msg = dict(Digits='1', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertIn('<Play>', rv.data)
        self.assertIn('egg-1.wav</Play>', rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('instructions</Redirect>', rv.data)

        # easter egg #2
        msg = dict(Digits='4', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertIn('<Play>', rv.data)
        self.assertIn('egg-2.wav</Play>', rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('instructions</Redirect>', rv.data)

        # easter egg #3
        msg = dict(Digits='7', From='+14155551212')
        rv = self.app.post(path, data=msg, follow_redirects=True)
        self.assertIn('<Play>', rv.data)
        self.assertIn('egg-3.wav</Play>', rv.data)
        self.assertIn('<Redirect>', rv.data)
        self.assertIn('instructions</Redirect>', rv.data)

    def get_and_post(self, path):
        return_values = []

        rv = self.app.get(path)
        return_values.append(rv)

        msg = {'From': '+14155551212'}
        rv = self.app.post(path, data=msg, follow_redirects=True)
        return_values.append(rv)
        return return_values

    def assertHasGather(self, text):
        self.assertIn('<Gather', text)
        self.assertIn('numDigits="1"', text)
        self.assertIn('action="http', text)
        self.assertIn('</Gather>', text)

    def test_voice_main(self):
        path = "/voice"
        for rv in self.get_and_post(path):
            self.assertIn('<Redirect>', rv.data)
            self.assertIn('instructions</Redirect>', rv.data)

    def test_voice_instructions(self):
        path = "/voice/instructions"
        for rv in self.get_and_post(path):
            self.assertHasGather(rv.data)
            self.assertIn('<Redirect>', rv.data)
            self.assertIn('prerendered-cat</Redirect>', rv.data)

    def test_voice_help(self):
        path = "/voice/help"
        for rv in self.get_and_post(path):
            self.assertHasGather(rv.data)
            self.assertIn('<Redirect>', rv.data)
            self.assertIn('instructions</Redirect>', rv.data)

    def test_voice_prerendered_cat(self):
        path = "/voice/random-prerendered-cat"
        for rv in self.get_and_post(path):
            self.assertHasGather(rv.data)
            self.assertIn('<Redirect>', rv.data)
            self.assertIn('<Play>', rv.data)
            self.assertIn('</Play>', rv.data)
            self.assertIn('prerendered-cat</Redirect>', rv.data)

    def test_voice_live_rendered_cat(self):
        path = "/voice/random-api-cat"
        for rv in self.get_and_post(path):
            self.assertHasGather(rv.data)
            self.assertIn('<Redirect>', rv.data)
            self.assertIn('<Play>', rv.data)
            self.assertIn('.wav</Play>', rv.data)
            self.assertIn('api-cat</Redirect>', rv.data)

    @unittest.skip("Not yet sure how to test this")
    def test_cat_sstv_wav(self):
        path = "/cat-api/v1/sstv-TEST.wav"
        rv = self.app.get(path)
        self.assertEquals('5661190', rv.headers['Content-Length'])
        self.assertIn('RIFF', rv.data)

    @unittest.skip("Not yet sure how to test this")
    def test_image_test(self):
        """tests the same code as cat_sstv_wav, but with a static image"""
        path = "/test.wav"
        rv = self.app.get(path)
        self.assertEquals('5661190', rv.headers['Content-Length'])
        self.assertIn('RIFF', rv.data)

    def test_easter_eggs(self):
        """easter eggs? hmm."""
        path = "/easter-egg-1.wav"
        rv = self.app.get(path)
        self.assertIn('<Play>', rv.data)
        self.assertIn('</Play>', rv.data)

        path = "/easter-egg-2.wav"
        rv = self.app.get(path)
        self.assertIn('<Play>', rv.data)
        self.assertIn('</Play>', rv.data)

        path = "/easter-egg-3.wav"
        rv = self.app.get(path)
        self.assertIn('<Play>', rv.data)
        self.assertIn('</Play>', rv.data)
