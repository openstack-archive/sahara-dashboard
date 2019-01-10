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

from oslo_log import log as logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs
from sahara_dashboard.content. \
    data_processing.utils import workflow_helpers as helpers
from sahara_dashboard.content.data_processing.clusters.nodegroup_templates \
    import tables as node_group_template_tables

LOG = logging.getLogger(__name__)


class NodeGroupTemplatesTab(sahara_tabs.SaharaTableTab):
    table_classes = (node_group_template_tables.NodegroupTemplatesTable, )
    name = _("Node Group Templates")
    slug = "node_group_templates_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_nodegroup_templates_data(self):
        try:
            table = self._tables['nodegroup_templates']
            search_opts = {}
            filter = self.get_server_filter_info(table.request, table)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            node_group_templates = saharaclient.nodegroup_template_list(
                self.request, search_opts)
        except Exception:
            node_group_templates = []
            exceptions.handle(self.request,
                              _("Unable to fetch node group template list"))
        return node_group_templates


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "nodegroup_template_details_tab"
    template_name = "nodegroup_templates/_details.html"

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.nodegroup_template_get(
                request, template_id)
        except Exception as e:
            template = {}
            LOG.error(
                "Unable to fetch node group template details: %s" % str(e))
            return {"template": template}

        try:
            flavor = nova.flavor_get(request, template.flavor_id)
        except Exception:
            flavor = {}
            exceptions.handle(request,
                              _("Unable to fetch flavor for template."))

        floating_ip_pool_name = None
        if template.floating_ip_pool:
            try:
                floating_ip_pool_name = self._get_floating_ip_pool_name(
                    request, template.floating_ip_pool)
            except Exception:
                exceptions.handle(request,
                                  _("Unable to fetch floating ip pools."))

        base_image_name = None
        if template.image_id:
            try:
                base_image_name = saharaclient.image_get(
                    request, template.image_id).name
            except Exception:
                exceptions.handle(request,
                                  _("Unable to fetch Base Image with id: %s.")
                                  % template.image_id)

        security_groups = helpers.get_security_groups(
            request, template.security_groups)

        if getattr(template, 'boot_from_volume', None) is None:
            show_bfv = False
        else:
            show_bfv = True

        return {"template": template, "flavor": flavor,
                "floating_ip_pool_name": floating_ip_pool_name,
                "base_image_name": base_image_name,
                "security_groups": security_groups,
                "show_bfv": show_bfv}

    def _get_floating_ip_pool_name(self, request, pool_id):
        pools = [pool for pool in neutron.floating_ip_pools_list(
            request) if pool.id == pool_id]

        return pools[0].name if pools else pool_id


class ConfigsTab(tabs.Tab):
    name = _("Service Configurations")
    slug = "nodegroup_template_service_configs_tab"
    template_name = "nodegroup_templates/_service_confs.html"

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.nodegroup_template_get(
                request, template_id)
        except Exception as e:
            template = {}
            LOG.error(
                "Unable to fetch node group template details: %s" % str(e))
        return {"template": template}


class NodegroupTemplateDetailsTabs(tabs.TabGroup):
    slug = "nodegroup_template_details"
    tabs = (GeneralTab, ConfigsTab, )
    sticky = True
