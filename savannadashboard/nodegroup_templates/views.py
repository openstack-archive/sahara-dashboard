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


from horizon import tables
from horizon import workflows
import logging

from savannadashboard.api import client as savannaclient

from savannadashboard.nodegroup_templates.tables \
    import NodegroupTemplatesTable
from savannadashboard.nodegroup_templates.workflows \
    import ConfigureNodegroupTemplate
from savannadashboard.nodegroup_templates.workflows \
    import CreateNodegroupTemplate

LOG = logging.getLogger(__name__)


class NodegroupTemplatesView(tables.DataTableView):
    table_class = NodegroupTemplatesTable
    template_name = 'nodegroup_templates/nodegroup_templates.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        nodegroup_templates = savanna.node_group_templates.list()
        return nodegroup_templates


class CreateNodegroupTemplateView(workflows.WorkflowView):
    workflow_class = CreateNodegroupTemplate
    success_url = \
        "horizon:savanna:nodegroup_templates:create-nodegroup-template"
    classes = ("ajax-modal")
    template_name = "nodegroup_templates/create.html"


class ConfigureNodegroupTemplateView(workflows.WorkflowView):
    workflow_class = ConfigureNodegroupTemplate
    success_url = "horizon:savanna:nodegroup_templates"
    template_name = "nodegroup_templates/configure.html"

    def get_context_data(self, **kwargs):
        context = super(ConfigureNodegroupTemplateView, self).get_context_data(
            **kwargs)

        context["plugin_name"] = self.request.session.get("plugin_name")
        context["plugin_version"] = self.request.session.get("plugin_version")

        return context
