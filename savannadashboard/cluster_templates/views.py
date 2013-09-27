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
from horizon import workflows

from savannadashboard.api.client import client as savannaclient
from savannadashboard.cluster_templates import forms as cluster_forms
from savannadashboard.cluster_templates.tables import ClusterTemplatesTable
import savannadashboard.cluster_templates.tabs as _tabs
import savannadashboard.cluster_templates.workflows.copy as copy_flow
import savannadashboard.cluster_templates.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class ClusterTemplatesView(tables.DataTableView):
    table_class = ClusterTemplatesTable
    template_name = 'cluster_templates/cluster_templates.html'

    def get_data(self):
        savanna = savannaclient(self.request)
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


class CreateClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.CreateClusterTemplate
    success_url = \
        "horizon:savanna:cluster_templates:create-cluster-template"
    classes = ("ajax-modal")
    template_name = "cluster_templates/create.html"


class ConfigureClusterTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureClusterTemplate
    success_url = "horizon:savanna:cluster_templates"
    template_name = "cluster_templates/configure.html"


class CopyClusterTemplateView(workflows.WorkflowView):
    workflow_class = copy_flow.CopyClusterTemplate
    success_url = "horizon:savanna:cluster_templates"
    template_name = "cluster_templates/configure.html"

    def get_context_data(self, **kwargs):
        context = super(CopyClusterTemplateView, self)\
            .get_context_data(**kwargs)

        context["template_id"] = kwargs["template_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['template_id']
            savanna = savannaclient(self.request)
            template = savanna.cluster_templates.get(template_id)
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(CopyClusterTemplateView, self).get_initial()
        initial.update({'template_id': self.kwargs['template_id']})
        return initial
