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
from openstack_dashboard.api import nova

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content. \
    data_processing.utils import workflow_helpers as helpers
from sahara_dashboard.content.data_processing.clusters.cluster_templates \
    import tables as cluster_template_tables
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs


LOG = logging.getLogger(__name__)


class ClusterTemplatesTab(sahara_tabs.SaharaTableTab):
    table_classes = (cluster_template_tables.ClusterTemplatesTable, )
    name = _("Cluster Templates")
    slug = "clusters_templates_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_cluster_templates_data(self):
        try:
            table = self._tables['cluster_templates']
            search_opts = {}
            filter = self.get_server_filter_info(table.request, table)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            cluster_templates = saharaclient.cluster_template_list(
                self.request, search_opts)
        except Exception:
            cluster_templates = []
            exceptions.handle(self.request,
                              _("Unable to fetch cluster template list"))
        return cluster_templates


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "cluster_template_details_tab"
    template_name = "cluster_templates/_details.html"

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.cluster_template_get(request, template_id)
        except Exception as e:
            template = {}
            LOG.error("Unable to fetch cluster template details: %s" % str(e))
        if saharaclient.VERSIONS.active == '2':
            template.hadoop_version = template.plugin_version
        return {"template": template}


class ClusterTemplateConfigsDetails(tabs.Tab):
    name = _("Configuration Details")
    slug = "cluster_template_configs_details_tab"
    template_name = (
        "cluster_templates/_cluster_template_configs_details.html")

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.cluster_template_get(request, template_id)
        except Exception as e:
            template = {}
            LOG.error("Unable to fetch cluster template details: %s" % str(e))
        return {"template": template}


class NodeGroupsTab(tabs.Tab):
    name = _("Node Groups")
    slug = "cluster_template_nodegroups_tab"
    template_name = "cluster_templates/_nodegroups_details.html"

    def get_context_data(self, request):
        template_id = self.tab_group.kwargs['template_id']
        try:
            template = saharaclient.cluster_template_get(request, template_id)
            for ng in template.node_groups:
                if not ng["flavor_id"]:
                    continue
                ng["flavor_name"] = (
                    nova.flavor_get(request, ng["flavor_id"]).name)
                ng["node_group_template"] = saharaclient.safe_call(
                    saharaclient.nodegroup_template_get,
                    request, ng.get("node_group_template_id", None))
                ng["security_groups_full"] = helpers.get_security_groups(
                    request, ng.get("security_groups"))
        except Exception:
            template = {}
            exceptions.handle(request,
                              _("Unable to fetch node group details."))
        return {"template": template}


class ClusterTemplateDetailsTabs(tabs.TabGroup):
    slug = "cluster_template_details"
    tabs = (GeneralTab, ClusterTemplateConfigsDetails, NodeGroupsTab, )
    sticky = True
