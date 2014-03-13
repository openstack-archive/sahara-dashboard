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

import json
import logging

from django.core.urlresolvers import reverse_lazy
from horizon import forms
from horizon import tables

from saharadashboard.api.client import client as saharaclient
from saharadashboard.image_registry.forms import EditTagsForm
from saharadashboard.image_registry.forms import RegisterImageForm
from saharadashboard.image_registry.tables import ImageRegistryTable


LOG = logging.getLogger(__name__)


class ImageRegistryView(tables.DataTableView):
    table_class = ImageRegistryTable
    template_name = 'image_registry/image_registry.html'

    def get_data(self):
        sahara = saharaclient(self.request)

        return sahara.images.list()


def update_context_with_plugin_tags(request, context):
        sahara = saharaclient(request)
        plugins = sahara.plugins.list()

        plugins_object = dict()
        for plugin in plugins:
            plugins_object[plugin.name] = dict()
            for version in plugin.versions:
                plugins_object[plugin.name][version] = []
                details = sahara.plugins.get_version_details(plugin.name,
                                                             version)

                for tag in details.required_image_tags:
                    plugins_object[plugin.name][version].append(tag)

        context["plugins"] = plugins_object
        return context


class EditTagsView(forms.ModalFormView):
    form_class = EditTagsForm
    template_name = 'image_registry/edit_tags.html'
    success_url = reverse_lazy('horizon:sahara:image_registry:index')

    def get_context_data(self, **kwargs):
        context = super(EditTagsView, self).get_context_data(**kwargs)
        context['image'] = self.get_object()
        context = update_context_with_plugin_tags(self.request, context)
        return context

    def get_object(self):
        sahara = saharaclient(self.request)
        return sahara.images.get(self.kwargs["image_id"])

    def get_initial(self):
        image = self.get_object()

        return {"image_id": image.id,
                "tags_list": json.dumps(image.tags),
                "user_name": image.username,
                "description": image.description}


class RegisterImageView(forms.ModalFormView):
    form_class = RegisterImageForm
    template_name = 'image_registry/register_image.html'
    success_url = reverse_lazy('horizon:sahara:image_registry:index')

    def get_context_data(self, **kwargs):
        context = super(RegisterImageView, self).get_context_data(**kwargs)
        context = update_context_with_plugin_tags(self.request, context)
        return context

    def get_initial(self):
        # need this initialization to allow registration
        # of images without tags
        return {"tags_list": json.dumps([])}
