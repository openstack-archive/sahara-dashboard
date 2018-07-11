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
from sahara_dashboard.api import sahara as saharaclient

from horizon import exceptions
from horizon import tables
from horizon import tabs
from openstack_dashboard.api import glance
from openstack_dashboard.api import neutron
from openstack_dashboard.api import nova

from sahara_dashboard.content.data_processing.clusters.clusters \
    import tables as cluster_tables
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs
from sahara_dashboard.content.data_processing.utils \
    import workflow_helpers as helpers

LOG = logging.getLogger(__name__)


class ClustersTab(sahara_tabs.SaharaTableTab):
    table_classes = (cluster_tables.ClustersTable, )
    name = _("Clusters")
    slug = "clusters_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_clusters_data(self):
        try:
            table = self._tables['clusters']
            search_opts = {}
            filter = self.get_server_filter_info(table.request, table)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            clusters = saharaclient.cluster_list(self.request, search_opts)
        except Exception:
            clusters = []
            exceptions.handle(self.request,
                              _("Unable to fetch cluster list"))
        return clusters


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "cluster_details_tab"
    template_name = "clusters/_details.html"

    def get_context_data(self, request):
        cluster_id = self.tab_group.kwargs['cluster_id']
        cluster_info = {}
        try:
            sahara = saharaclient.client(request)
            cluster = sahara.clusters.get(cluster_id)
            for info_key, info_val in cluster.info.items():
                for key, val in info_val.items():
                    if str(val).startswith(('http://', 'https://')):
                        cluster.info[info_key][key] = build_link(val)

            try:
                base_image = glance.image_get(request,
                                              cluster.default_image_id)
            except Exception:
                exceptions.handle(
                    request, _("Unable to fetch base image details"))
                base_image = {}

            if getattr(cluster, 'cluster_template_id', None):
                cluster_template = saharaclient.safe_call(
                    sahara.cluster_templates.get,
                    cluster.cluster_template_id)
            else:
                cluster_template = None
            try:
                if getattr(cluster, 'neutron_management_network', None):
                    net_id = cluster.neutron_management_network
                    network = neutron.network_get(request, net_id)
                    net_name = network.name_or_id
                else:
                    net_name = None
            except Exception:
                exceptions.handle(
                    request, _("Unable to fetch network details"))
                net_name = None

            cluster_info.update({"cluster": cluster,
                                 "base_image": base_image,
                                 "cluster_template": cluster_template,
                                 "network": net_name})

            if saharaclient.VERSIONS.active == '2':
                cluster_info["cluster"].hadoop_version = (
                    cluster_info["cluster"].plugin_version
                )
        except Exception as e:
            LOG.error("Unable to fetch cluster details: %s" % str(e))

        return cluster_info


class ClusterConfigsDetails(tabs.Tab):
    name = _("Configuration Details")
    slug = "cluster_configs_details_tab"
    template_name = (
        "clusters/_cluster_configs_details.html")

    def get_context_data(self, request):
        cluster_id = self.tab_group.kwargs['cluster_id']
        cluster = {}
        try:
            sahara = saharaclient.client(request)
            cluster = sahara.clusters.get(cluster_id)

        except Exception as e:
            LOG.error("Unable to fetch cluster details: %s" % str(e))

        return {'cluster': cluster}


def build_link(url):
    return "<a href='" + url + "' target=\"_blank\">" + url + "</a>"


class NodeGroupsTab(tabs.Tab):
    name = _("Node Groups")
    slug = "cluster_nodegroups_tab"
    template_name = "clusters/_nodegroups_details.html"

    def get_context_data(self, request):
        cluster_id = self.tab_group.kwargs['cluster_id']
        try:
            sahara = saharaclient.client(request)
            cluster = sahara.clusters.get(cluster_id)
            for ng in cluster.node_groups:
                if ng["flavor_id"]:
                    ng["flavor_name"] = (
                        nova.flavor_get(request, ng["flavor_id"]).name)
                if ng["floating_ip_pool"]:
                    ng["floating_ip_pool_name"] = (
                        self._get_floating_ip_pool_name(
                            request, ng["floating_ip_pool"]))

                if ng.get("node_group_template_id", None):
                    ng["node_group_template"] = saharaclient.safe_call(
                        sahara.node_group_templates.get,
                        ng["node_group_template_id"])

                ng["security_groups_full"] = helpers.get_security_groups(
                    request, ng["security_groups"])
        except Exception:
            cluster = {}
            exceptions.handle(request,
                              _("Unable to get node group details."))

        return {"cluster": cluster}

    def _get_floating_ip_pool_name(self, request, pool_id):
        pools = [pool for pool in neutron.floating_ip_pools_list(
            request) if pool.id == pool_id]

        return pools[0].name if pools else pool_id


class Instance(object):
    def __init__(self, name=None, id=None, internal_ip=None,
                 management_ip=None):
        self.name = name
        self.id = id
        self.internal_ip = internal_ip
        self.management_ip = management_ip


class InstancesTable(tables.DataTable):
    name = tables.Column("name",
                         link="horizon:project:instances:detail",
                         verbose_name=_("Name"))

    internal_ip = tables.Column("internal_ip",
                                verbose_name=_("Internal IP"))

    management_ip = tables.Column("management_ip",
                                  verbose_name=_("Management IP"))

    class Meta(object):
        name = "cluster_instances"
        verbose_name = _("Cluster Instances")


class InstancesTab(tabs.TableTab):
    name = _("Instances")
    slug = "cluster_instances_tab"
    template_name = "clusters/_instances_details.html"
    table_classes = (InstancesTable, )

    def get_cluster_instances_data(self):
        cluster_id = self.tab_group.kwargs['cluster_id']

        try:
            sahara = saharaclient.client(self.request)
            cluster = sahara.clusters.get(cluster_id)

            instances = []
            for ng in cluster.node_groups:
                for instance in ng["instances"]:
                    instances.append(Instance(
                        name=instance["instance_name"],
                        id=instance["instance_id"],
                        internal_ip=instance.get("internal_ip",
                                                 "Not assigned"),
                        management_ip=instance.get("management_ip",
                                                   "Not assigned")))
        except Exception:
            instances = []
            exceptions.handle(self.request,
                              _("Unable to fetch instance details."))
        return instances


class EventLogTab(tabs.Tab):
    name = _("Cluster Events")
    slug = "cluster_event_log"
    template_name = "clusters/_event_log.html"

    def get_context_data(self, request, **kwargs):
        cluster_id = self.tab_group.kwargs['cluster_id']
        kwargs["cluster_id"] = cluster_id
        kwargs['data_update_url'] = request.get_full_path()

        return kwargs


class HealthChecksTab(tabs.Tab):
    name = _("Cluster health checks")
    slug = 'cluster_health_checks'
    template_name = "clusters/_health_checks_table.html"

    def get_context_data(self, request, **kwargs):
        cluster_id = self.tab_group.kwargs['cluster_id']
        kwargs['cluster_id'] = cluster_id
        kwargs['data_update_url'] = request.get_full_path()
        return kwargs


class ClusterDetailsTabs(tabs.TabGroup):
    slug = "cluster_details"
    if saharaclient.SAHARA_VERIFICATION_DISABLED:
        tabs = (GeneralTab, ClusterConfigsDetails, NodeGroupsTab, InstancesTab,
                EventLogTab)
    else:
        tabs = (GeneralTab, ClusterConfigsDetails, NodeGroupsTab, InstancesTab,
                EventLogTab, HealthChecksTab)

    sticky = True
