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

from django import http as http_response
from django.template import defaultfilters as filters
from django import urls
from django.utils import http
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.tabs import base as tabs_base
from oslo_serialization import jsonutils as json

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing \
    import tables as sahara_table
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils


class ClusterTemplatesFilterAction(tables.FilterAction):
    filter_type = "server"
    filter_choices = (('name', _("Name"), True),
                      ('plugin_name', _("Plugin"), True),
                      ('hadoop_version', _("Version"), True),
                      ('description', _("Description")))


class CreateCluster(tables.LinkAction):
    name = "create cluster"
    verbose_name = _("Launch Cluster")
    url = "horizon:project:data_processing.clusters:configure-cluster"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = urls.reverse(self.url)

        if saharaclient.VERSIONS.active == '2':
            version_attr = "plugin_version"
        else:
            version_attr = "hadoop_version"
        params = http.urlencode({"hadoop_version":
                                 getattr(datum, version_attr),
                                 "plugin_name": datum.plugin_name,
                                 "cluster_template_id": datum.id})
        return "?".join([base_url, params])


class CopyTemplate(tables.LinkAction):
    name = "copy"
    verbose_name = _("Copy Template")
    url = "horizon:project:data_processing.clusters:ct-copy"
    classes = ("ajax-modal", )


class ExportTemplate(tables.Action):
    name = "export"
    verbose_name = _("Export Template")
    classes = ("ajax-modal", )

    def single(self, data_table, request, object_id):
        content = json.dumps(saharaclient.cluster_template_export(
            request, object_id)._info)
        response = http_response.HttpResponse(
            content, content_type="application/json")
        filename = '%s-cluster-template.json' % object_id
        disposition = 'attachment; filename="%s"' % filename
        response['Content-Disposition'] = disposition.encode('utf-8')
        response['Content-Length'] = str(len(response.content))
        return response


class EditTemplate(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit Template")
    url = "horizon:project:data_processing.clusters:ct-edit"
    classes = ("ajax-modal", )


class DeleteTemplate(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Template",
            u"Delete Templates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Template",
            u"Deleted Templates",
            count
        )

    def delete(self, request, template_id):
        saharaclient.cluster_template_delete(request, template_id)


class CreateClusterTemplate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Template")
    url = ("horizon:project:data_processing.clusters:"
           "create-cluster-template")
    classes = ("ajax-modal", "create-clustertemplate-btn")
    icon = "plus"


class ImportClusterTemplate(tables.LinkAction):
    name = "import"
    verbose_name = _("Import Template")
    url = ("horizon:project:data_processing.clusters:"
           "import-cluster-template-file")
    classes = ("ajax-modal",)
    icon = "plus"


class ConfigureClusterTemplate(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Cluster Template")
    url = ("horizon:project:data_processing.clusters:"
           "configure-cluster-template")
    classes = ("ajax-modal", "configure-clustertemplate-btn")
    icon = "plus"
    attrs = {"style": "display: none"}


def render_node_groups(cluster_template):
    node_groups = [node_group['name'] + ': ' + str(node_group['count'])
                   for node_group in cluster_template.node_groups]
    return node_groups


class MakePublic(acl_utils.MakePublic):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_template_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakePrivate(acl_utils.MakePrivate):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_template_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakeProtected(acl_utils.MakeProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_template_update_acl_rules(
            request, datum_id, **update_kwargs)


class MakeUnProtected(acl_utils.MakeUnProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.cluster_template_update_acl_rules(
            request, datum_id, **update_kwargs)


class ClusterTemplatesTable(sahara_table.SaharaPaginateTabbedTable):
    tab_name = 'cluster_tabs%sclusters_templates_tab' % tabs_base.SEPARATOR

    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:project:data_processing."
                               "clusters:ct-details"))
    plugin_name = tables.Column("plugin_name",
                                verbose_name=_("Plugin"))
    if saharaclient.VERSIONS.active == '2':
        version_attr = "plugin_version"
    else:
        version_attr = "hadoop_version"
    hadoop_version = tables.Column(version_attr,
                                   verbose_name=_("Version"))
    node_groups = tables.Column(render_node_groups,
                                verbose_name=_("Node Groups"),
                                wrap_list=True,
                                filters=(filters.unordered_list,))
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "cluster_templates"
        verbose_name = _("Cluster Templates")
        table_actions = (CreateClusterTemplate,
                         ImportClusterTemplate,
                         ConfigureClusterTemplate,
                         DeleteTemplate,
                         ClusterTemplatesFilterAction,)
        table_actions_menu = (MakePublic, MakePrivate,
                              MakeProtected, MakeUnProtected)
        row_actions = (CreateCluster,
                       EditTemplate,
                       CopyTemplate,
                       ExportTemplate,
                       DeleteTemplate, MakePublic, MakePrivate,
                       MakeProtected, MakeUnProtected)
