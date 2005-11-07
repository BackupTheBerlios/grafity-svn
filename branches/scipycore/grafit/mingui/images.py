from base import Singleton
import os

class DirImageProvider(object):
    def __init__(self, dir):
        self.dir = dir
        files = [os.path.join(dir, f) for f in os.listdir(dir)
                                       if os.path.isfile(os.path.join(dir, f))]
        ids = [os.path.splitext(os.path.basename(f))[0] for f in files]
        self.ids = dict(zip(ids, files))

    def provide(self, id):
        if id in self.ids:
            return PIL.Image.open(self.ids[id])
        else:
            return None

class ImageCatalog(Singleton):
    def __init__(self):
        if not hasattr(self, 'images'):
            self.images = {}
            self.providers = []

    def __getitem__(self, id):
        if id not in self.images:
            for p in self.providers:
                img = p.provide(id)
                if img is not None:
                    self.register(id, img)
        return self.images[id]

    def register(self, id, image):
        self.images.setdefault(id, {})[image.size] = image

    def register_dir(self, dir):
        self.providers.append(DirImageProvider(dir))

images = ImageCatalog()

