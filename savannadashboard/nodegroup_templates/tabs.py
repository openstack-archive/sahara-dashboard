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
from horizon.api import nova

from django.utils.translation import ugettext_lazy as _

import logging

from horizon import tabs
from savannadashboard.api import client as savannaclient

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General info")
    slug = "nodegroup_template_details_tab"
    template_name = ("nodegroup_templates/_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        savanna = savannaclient.Client(request)
        template = savanna.node_group_templates.get(template_id)
        flavor = nova.flavor_get(request, template.flavor_id)
        return {"template": template, "flavor": flavor}


class ConfigsTab(tabs.Tab):
    name = _("Service configurations")
    slug = "nodegroup_template_service_configs_tab"
    template_name = ("nodegroup_templates/_service_confs.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        savanna = savannaclient.Client(request)
        template = savanna.node_group_templates.get(template_id)
        return {"template": template}


class NodegroupTemplateDetailsTabs(tabs.TabGroup):
    slug = "nodegroup_template_details"
    tabs = (GeneralTab, ConfigsTab, )
    sticky = True