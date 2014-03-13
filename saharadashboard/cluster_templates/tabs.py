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

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from saharadashboard.api.client import client as saharaclient
from saharadashboard.utils import importutils
from saharadashboard.utils import workflow_helpers as helpers
nova = importutils.import_any('openstack_dashboard.api.nova',
                              'horizon.api.nova')

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "cluster_template_details_tab"
    template_name = ("cluster_templates/_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        sahara = saharaclient(request)
        template = sahara.cluster_templates.get(template_id)
        return {"template": template}


class NodeGroupsTab(tabs.Tab):
    name = _("Node Groups")
    slug = "cluster_template_nodegroups_tab"
    template_name = ("cluster_templates/_nodegroups_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        sahara = saharaclient(request)
        template = sahara.cluster_templates.get(template_id)
        for ng in template.node_groups:
            if not ng["flavor_id"]:
                continue
            ng["flavor_name"] = nova.flavor_get(request, ng["flavor_id"]).name
            ng["node_group_template"] = helpers.safe_call(
                sahara.node_group_templates.get,
                ng.get("node_group_template_id", None))
        return {"template": template}


class ClusterTemplateDetailsTabs(tabs.TabGroup):
    slug = "cluster_template_details"
    tabs = (GeneralTab, NodeGroupsTab, )
    sticky = True
