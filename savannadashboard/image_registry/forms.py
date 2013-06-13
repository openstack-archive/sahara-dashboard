# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils.translation import ugettext_lazy as _
from horizon import api
from horizon import exceptions
from horizon import forms
import json

from savannadashboard.api import client as savannaclient


class ImageForm(forms.SelfHandlingForm):
    image_id = forms.CharField(widget=forms.HiddenInput())
    tags_list = forms.CharField(widget=forms.HiddenInput())
    user_name = forms.CharField(max_length=80, label=_("User Name"))
    description = forms.CharField(max_length=80,
                                  label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea(attrs={'cols': 80,
                                                               'rows': 20}))

    def handle(self, request, data):
        try:
            savanna = savannaclient.Client(request)

            image_id = data['image_id']
            user_name = data['user_name']
            desc = data['description']
            savanna.images.update_image(image_id, user_name, desc)

            image_tags = json.loads(data["tags_list"])
            savanna.images.update_tags(image_id, image_tags)

            return True
        except Exception:
            exceptions.handle(request)
            return False


class EditTagsForm(ImageForm):
    image_id = forms.CharField(widget=forms.HiddenInput())


class RegisterImageForm(ImageForm):
    image_id = forms.ChoiceField(label=_("Image"),
                                 required=True)

    def __init__(self, request, *args, **kwargs):
        super(RegisterImageForm, self).__init__(request, *args, **kwargs)
        self._populate_image_id_choices()

    def _populate_image_id_choices(self):
        images = self._get_available_images(self.request)
        choices = [(image.id, image.name)
                   for image in images
                   if image.properties.get("image_type", '') != "snapshot"]
        if choices:
            choices.insert(0, ("", _("Select Image")))
        else:
            choices.insert(0, ("", _("No images available.")))
        self.fields['image_id'].choices = choices

    def get_images(self, request):
        public = {"is_public": True,
                  "status": "active"}
        try:
            imgs = api.glance.image_list_detailed(request, filters=public)
            public_images, _more = imgs
        except Exception:
            public_images = []
            exceptions.handle(request,
                              _("Unable to retrieve public images."))
        self._public_images = public_images

    def _get_available_images(self, request):

        if not hasattr(self, "_public_images"):
            self.get_images(request)

        final_images = []

        savanna = savannaclient.Client(request)
        image_ids = [img.id for img in savanna.images.list()]

        for image in self._public_images:
            if image.id not in image_ids:
                image_ids.append(image.id)
                final_images.append(image)
        return [image for image in final_images
                if image.container_format
                not in ('aki', 'ari')]
