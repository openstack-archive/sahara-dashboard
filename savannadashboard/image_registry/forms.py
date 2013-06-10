import json

from horizon import exceptions
from horizon import forms

from savannadashboard.api import client as savannaclient


class EditTagsForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    tags_list = forms.CharField(widget=forms.HiddenInput())

    def handle(self, request, data):
        try:
            savanna = savannaclient.Client(request)

            image_id = data['image_id']
            image_tags = json.loads(data["tags_list"])

            savanna.images.update_tags(image_id, image_tags)

            return True
        except Exception:
            exceptions.handle(request)
            return False
