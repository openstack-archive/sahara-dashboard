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

from collections import OrderedDict
import json

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content. \
    data_processing.clusters.image_registry.forms import EditTagsForm
from sahara_dashboard.content. \
    data_processing.clusters.image_registry.forms import RegisterImageForm
from sahara_dashboard import utils


def update_context_with_plugin_tags(request, context):
    try:
        plugins = saharaclient.plugin_list(request)
    except Exception:
        plugins = []
        msg = _("Unable to process plugin tags")
        exceptions.handle(request, msg)

    plugins_object = dict()
    for plugin in plugins:
        plugins_object[plugin.name] = OrderedDict()
        for version in sorted(plugin.versions, reverse=True,
                              key=utils.smart_sort_helper):
            try:
                details = saharaclient. \
                    plugin_get_version_details(request,
                                               plugin.name,
                                               version)
                plugins_object[plugin.name][version] = (
                    details.required_image_tags)
            except Exception:
                msg = _("Unable to process plugin tags")
                exceptions.handle(request, msg)

    context["plugins"] = plugins_object


class EditTagsView(forms.ModalFormView):
    form_class = EditTagsForm
    template_name = 'image_registry/edit_tags.html'
    success_url = reverse_lazy(
        'horizon:project:data_processing.clusters:index')
    page_title = _("Edit Image Tags")

    def get_context_data(self, **kwargs):
        context = super(EditTagsView, self).get_context_data(**kwargs)
        context['image'] = self.get_object()
        update_context_with_plugin_tags(self.request, context)
        return context

    @memoized.memoized_method
    def get_object(self):
        try:
            image = saharaclient.image_get(self.request,
                                           self.kwargs["image_id"])
        except Exception:
            image = None
            msg = _("Unable to fetch the image details")
            exceptions.handle(self.request, msg)
        return image

    def get_initial(self):
        image = self.get_object()

        return {"image_id": image.id,
                "tags_list": json.dumps(image.tags),
                "user_name": image.username,
                "description": image.description}


class RegisterImageView(forms.ModalFormView):
    form_class = RegisterImageForm
    template_name = 'image_registry/register_image.html'
    success_url = reverse_lazy(
        'horizon:project:data_processing.clusters:index')
    page_title = _("Register Image")

    def get_context_data(self, **kwargs):
        context = super(RegisterImageView, self).get_context_data(**kwargs)
        context['action_url'] = ('horizon:project'
                                 ':data_processing.clusters:register')
        update_context_with_plugin_tags(self.request, context)
        return context

    def get_initial(self):
        # need this initialization to allow registration
        # of images without tags
        return {"tags_list": json.dumps([])}
