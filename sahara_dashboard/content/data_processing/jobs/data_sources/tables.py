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

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.tabs import base as tabs_base

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing \
    import tables as sahara_table
from sahara_dashboard.content.data_processing.utils \
    import acl as acl_utils


class CreateDataSource(tables.LinkAction):
    name = "create data source"
    verbose_name = _("Create Data Source")
    url = "horizon:project:data_processing.jobs:create-data-source"
    classes = ("ajax-modal",)
    icon = "plus"


class DeleteDataSource(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Data Source",
            u"Delete Data Sources",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Data Source",
            u"Deleted Data Sources",
            count
        )

    def delete(self, request, obj_id):
        saharaclient.data_source_delete(request, obj_id)


class EditDataSource(tables.LinkAction):
    name = "edit data source"
    verbose_name = _("Edit Data Source")
    url = "horizon:project:data_processing.jobs:edit-data-source"
    classes = ("ajax-modal",)


class MakePublic(acl_utils.MakePublic):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.data_source_update(
            request, datum_id, update_kwargs)


class MakePrivate(acl_utils.MakePrivate):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.data_source_update(
            request, datum_id, update_kwargs)


class MakeProtected(acl_utils.MakeProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.data_source_update(
            request, datum_id, update_kwargs)


class MakeUnProtected(acl_utils.MakeUnProtected):
    def change_rule_method(self, request, datum_id, **update_kwargs):
        saharaclient.data_source_update(
            request, datum_id, update_kwargs)


class DataSourcesTable(sahara_table.SaharaPaginateTabbedTable):
    tab_name = 'job_tabs%sdata_sources_tab' % tabs_base.SEPARATOR
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link=("horizon:project:data_processing."
                               "jobs:ds-details"))
    type = tables.Column("type",
                         verbose_name=_("Type"))
    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "data_sources"
        verbose_name = _("Data Sources")
        table_actions = (CreateDataSource,
                         DeleteDataSource)
        table_actions_menu = (MakePublic,
                              MakePrivate,
                              MakeProtected,
                              MakeUnProtected)
        row_actions = (DeleteDataSource,
                       EditDataSource,
                       MakePublic,
                       MakePrivate,
                       MakeProtected,
                       MakeUnProtected)
