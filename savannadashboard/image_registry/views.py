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

from django.core.urlresolvers import reverse_lazy
from horizon import forms
from horizon import tables
import json
import logging
from savannadashboard.image_registry.forms import EditTagsForm
from savannadashboard.image_registry.tables import ImageRegistryTable
from savannadashboard.utils.restclient import get_image_by_id
from savannadashboard.utils.restclient import get_images


LOG = logging.getLogger(__name__)


class EditTagsView(forms.ModalFormView):
    form_class = EditTagsForm
    template_name = 'image_registry/edit_tags.html'
    success_url = reverse_lazy('horizon:savanna:image_registry:index')

    def get_context_data(self, **kwargs):
        context = super(EditTagsView, self).get_context_data(**kwargs)
        context['image'] = self.get_object()
        return context

    def get_object(self):
        return get_image_by_id(self.request, self.kwargs["image_id"])

    def get_initial(self):
        image = self.get_object()
        return {"image_id": image.id, "tags_list": json.dumps(image.tags)}


class ImageRegistryView(tables.DataTableView):
    table_class = ImageRegistryTable
    template_name = 'image_registry/image_registry.html'

    def get_data(self):
        return get_images(self.request)
