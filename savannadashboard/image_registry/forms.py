import json

from horizon import exceptions
from horizon import forms
from savannadashboard.utils.restclient import add_image_tags
from savannadashboard.utils.restclient import get_image_by_id
from savannadashboard.utils.restclient import remove_image_tags


class EditTagsForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    tags_list = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            image = get_image_by_id(request, data['image_id'])
            oldtags = frozenset(image.tags)
            updatedtags = frozenset(json.loads(data["tags_list"]))

            to_add = list(updatedtags - oldtags)
            to_remove = list(oldtags - updatedtags)

            if (len(to_add) != 0):
                add_image_tags(request, data['image_id'], to_add)

            if (len(to_remove) != 0):
                remove_image_tags(request, data['image_id'], to_remove)

            return True
        except Exception:
            exceptions.handle(request)
            return False
