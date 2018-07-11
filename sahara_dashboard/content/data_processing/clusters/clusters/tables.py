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

from django.http import Http404  # noqa
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy
from saharaclient.api import base as api_base

from horizon import messages
from horizon import tables
from horizon.tables import base as tables_base
from horizon.tabs import base as tabs_base

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing \
    import tables as sahara_table
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils
from sahara_dashboard.content.data_processing.utils import helpers

SAHARA_VERIFICATION_DISABLED = saharaclient.SAHARA_VERIFICATION_DISABLED


class ClustersFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('name', _("Name"), True),
                      ('status', _("Status"), True))


class ClusterGuide(tables.LinkAction):
    name = "cluster_guide"
    verbose_name = _("Cluster Creation Guide")
    url = "horizon:project:data_processing.clusters:cluster_guide"


class CreateCluster(tables.LinkAction):
    name = "create"
    verbose_name = _("Launch Cluster")
    url = "horizon:project:data_processing.clusters:create-cluster"
    classes = ("ajax-modal",)
    icon = "plus"


class ScaleCluster(tables.LinkAction):
    name = "scale"
    verbose_name = _("Scale Cluster")
    url = "horizon:project:data_processing.clusters:scale"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, cluster=None):
        return cluster.status == "Active"


class DeleteCluster(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Cluster",
            u"Delete Clusters",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Cluster",
            u"Deleted Clusters",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.cluster_delete(request, obj_id)


class CheckClusterAction(tables.BatchAction):
    name = 'check_cluster'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Start Verification",
            u"Start Verifications",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Started Verification",
            u"Started Verifications",
            count
        )

    def action(self, request, datum_id):
        saharaclient.verification_update(request, datum_id, status='START')


class ForceDeleteCluster(tables.DeleteAction):
    name = "force_delete"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Force Delete Cluster",
            u"Force Delete Clusters",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Force Deleted Cluster",
            u"Force Deleted Clusters",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.cluster_force_delete(request, obj_id)


class UpdateClusterShares(tables.LinkAction):
    name = "update_shares"
    verbose_name = _("Update Shares")
    url = "horizon:project:data_processing.clusters:update-shares"
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, cluster=None):
        return cluster.status == "Active"


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        try:
            return saharaclient.cluster_get(request, instance_id)
        except api_base.APIException as e:
            if e.error_code == 404:
                raise Http404
            else:
                messages.error(request,
                               _("Unable to update row"))


def get_instances_count(cluster):
    return sum([len(ng["instances"])
                for ng in cluster.node_groups])


class RichErrorCell(tables_base.Cell):
    @property
    def status(self):
        # The error cell values becomes quite complex and cannot be handled
        # correctly with STATUS_CHOICES. Handling that explicitly.
        status = self.datum.status.lower()
        health = get_health_status_info(self.datum).lower()
        # error status always terminal
        if status == "error":
            return False
        if health == 'checking' or health == 'unknown':
            return None
        if status == "active":
            return True
        return None


def get_rich_status_info(cluster):
    return {
        "status": cluster.status,
        "status_description": cluster.status_description
    }


def rich_status_filter(status_dict):
    if status_dict['status'].lower() not in ['error', 'active']:
        return render_to_string("clusters/_in_progress.html", status_dict)
    # Render the status "as is" if no description is provided.
    if status_dict["status_description"]:
        # Error is rendered with a template containing an error description.
        return render_to_string("clusters/_rich_status.html", status_dict)
    return status_dict["status"]


class ConfigureCluster(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Cluster")
    url = "horizon:project:data_processing.clusters:configure-cluster"
    classes = ("ajax-modal", "configure-cluster-btn")
    icon = "plus"
    attrs = {"style": "display: none"}


class MakePublic(acl_utils.MakePublic):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakePrivate(acl_utils.MakePrivate):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakeProtected(acl_utils.MakeProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakeUnProtected(acl_utils.MakeUnProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_update_acl_rules(
            request, datum_id, **update_kwargs)


def get_health_status_info(cluster):
    try:
        return cluster.verification['status']
    except (AttributeError, KeyError):
        return 'UNKNOWN'


def get_health_filter(health):
    if health == 'CHECKING':
        return render_to_string("clusters/_in_progress.html", {
            'status': _("Checking")})
    mapper = {'GREEN': 'success', 'YELLOW': 'warning',
              'RED': 'danger', 'CHECKING': 'info'}

    label = mapper.get(health, 'default')
    return render_to_string('clusters/_health_status.html',
                            {'status': health, 'label': label})


class ClustersTable(sahara_table.SaharaPaginateTabbedTable):

    tab_name = 'cluster_tabs%sclusters_tab' % tabs_base.SEPARATOR

    class UptimeColumn(tables.Column):
        def get_data(self, cluster):
            return helpers.Helpers(None).get_duration(cluster.created_at)

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:project:data_processing."
                               "clusters:cluster-details"))

    plugin = tables.Column("plugin_name",
                           verbose_name=_("Plugin"))

    if saharaclient.VERSIONS.active == '2':
        version_attr = "plugin_version"
    else:
        version_attr = "hadoop_version"
    version = tables.Column(version_attr,
                            verbose_name=_("Version"))

    # Status field need the whole cluster object to build the rich status.
    status = tables.Column(get_rich_status_info,
                           verbose_name=_("Status"),
                           filters=(rich_status_filter,))
    if not SAHARA_VERIFICATION_DISABLED:
        health = tables.Column(get_health_status_info,
                               verbose_name=_("Health"),
                               filters=(get_health_filter,))

    instances_count = tables.Column(get_instances_count,
                                    verbose_name=_("Instances Count"))

    uptime = UptimeColumn("uptime",
                          verbose_name=_("Uptime"))

    class Meta(object):
        name = "clusters"
        verbose_name = _("Clusters")
        row_class = UpdateRow
        cell_class = RichErrorCell
        status_columns = ["status"]
        if not SAHARA_VERIFICATION_DISABLED:
            status_columns.append("health")
        table_actions = (ClusterGuide,
                         CreateCluster,
                         ConfigureCluster,
                         DeleteCluster,
                         ClustersFilterAction)
        if saharaclient.VERSIONS.active == '2':
            table_actions = table_actions + (ForceDeleteCluster,)
        table_actions_menu = (MakePublic, MakePrivate,
                              MakeProtected, MakeUnProtected)
        if SAHARA_VERIFICATION_DISABLED:
            row_actions = (ScaleCluster,
                           UpdateClusterShares,
                           DeleteCluster, MakePublic, MakePrivate,
                           MakeProtected, MakeUnProtected)
        else:
            row_actions = (ScaleCluster,
                           UpdateClusterShares,
                           DeleteCluster, MakePublic, MakePrivate,
                           MakeProtected, MakeUnProtected,
                           CheckClusterAction)
        if saharaclient.VERSIONS.active == '2':
            row_actions = row_actions + (ForceDeleteCluster,)
