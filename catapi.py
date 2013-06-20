from PIL import Image
from StringIO import StringIO
import re
import requests


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
