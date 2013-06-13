import json

from savannadashboard.api import base


class Image(base.Resource):
    resource_name = 'Image'


class ImageManager(base.ResourceManager):
    resource_class = Image

    def list(self):
        return self._list('/images', 'images')

    def get(self, id):
        return self._get('/images/%s' % id, 'image')

    def update_image(self, image_id, user_name, desc):
        body = {"username": user_name,
                "description": desc}

        resp = self.api.client.post('/images/%s' % image_id, json.dumps(body))
        if resp.status_code != 202:
            raise RuntimeError('Failed to register image %s' % image_id)

    def update_tags(self, image_id, new_tags):
        old_image = self.get(image_id)

        old_tags = frozenset(old_image.tags)
        new_tags = frozenset(new_tags)

        to_add = list(new_tags - old_tags)
        to_remove = list(old_tags - new_tags)

        if len(to_add) != 0:
            resp = self.api.client.post('/images/%s/tag' % image_id,
                                        json.dumps({'tags': to_add}))

            if resp.status_code != 202:
                raise RuntimeError('Failed to add tags to image %s' % image_id)

        if len(to_remove) != 0:
            resp = self.api.client.post('/images/%s/untag' % image_id,
                                        json.dumps({'tags': to_remove}))

            if resp.status_code != 202:
                raise RuntimeError('Failed to remove tags from image %s' %
                                   image_id)
