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

import logging

from django.core.urlresolvers import reverse_lazy
from horizon import forms
from horizon import tables
from horizon import tabs

from savannadashboard.api import client as savannaclient
from savannadashboard.cluster_templates import forms as cluster_forms
from savannadashboard.cluster_templates.tables import ClusterTemplatesTable
import savannadashboard.cluster_templates.tabs as _tabs

LOG = logging.getLogger(__name__)


class ClusterTemplatesView(tables.DataTableView):
    table_class = ClusterTemplatesTable
    template_name = 'cluster_templates/cluster_templates.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        cluster_templates = savanna.cluster_templates.list()
        return cluster_templates


class ClusterTemplateDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterTemplateDetailsTabs
    template_name = 'cluster_templates/details.html'

    def get_context_data(self, **kwargs):
        context = super(ClusterTemplateDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class UploadFileView(forms.ModalFormView):
    form_class = cluster_forms.UploadFileForm
    template_name = 'cluster_templates/upload_file.html'
    success_url = reverse_lazy('horizon:savanna:cluster_templates:index')
