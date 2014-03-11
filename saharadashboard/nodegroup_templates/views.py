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

from horizon import tables
from horizon import tabs
from horizon import workflows

from saharadashboard.api.client import client as savannaclient

import saharadashboard.nodegroup_templates.tables as _tables
import saharadashboard.nodegroup_templates.tabs as _tabs
import saharadashboard.nodegroup_templates.workflows.copy as copy_flow
import saharadashboard.nodegroup_templates.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class NodegroupTemplatesView(tables.DataTableView):
    table_class = _tables.NodegroupTemplatesTable
    template_name = 'nodegroup_templates/nodegroup_templates.html'

    def get_data(self):
        savanna = savannaclient(self.request)
        nodegroup_templates = savanna.node_group_templates.list()
        return nodegroup_templates


class NodegroupTemplateDetailsView(tabs.TabView):
    tab_group_class = _tabs.NodegroupTemplateDetailsTabs
    template_name = 'nodegroup_templates/details.html'

    def get_context_data(self, **kwargs):
        context = super(NodegroupTemplateDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class CreateNodegroupTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.CreateNodegroupTemplate
    success_url = \
        "horizon:savanna:nodegroup_templates:create-nodegroup-template"
    classes = ("ajax-modal")
    template_name = "nodegroup_templates/create.html"


class ConfigureNodegroupTemplateView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureNodegroupTemplate
    success_url = "horizon:savanna:nodegroup_templates"
    template_name = "nodegroup_templates/configure.html"


class CopyNodegroupTemplateView(workflows.WorkflowView):
    workflow_class = copy_flow.CopyNodegroupTemplate
    success_url = "horizon:savanna:nodegroup_templates"
    template_name = "nodegroup_templates/configure.html"

    def get_context_data(self, **kwargs):
        context = super(CopyNodegroupTemplateView, self)\
            .get_context_data(**kwargs)

        context["template_id"] = kwargs["template_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['template_id']
            savanna = savannaclient(self.request)
            template = savanna.node_group_templates.get(template_id)
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(CopyNodegroupTemplateView, self).get_initial()
        initial.update({'template_id': self.kwargs['template_id']})
        return initial
