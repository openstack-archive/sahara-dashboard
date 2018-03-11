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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.jobs. \
    data_sources.tables as ds_tables
import sahara_dashboard.content.data_processing.jobs. \
    data_sources.tabs as _tabs
import sahara_dashboard.content.data_processing.jobs. \
    data_sources.workflows.create as create_flow
import sahara_dashboard.content.data_processing.jobs. \
    data_sources.workflows.edit as edit_flow


class CreateDataSourceView(workflows.WorkflowView):
    workflow_class = create_flow.CreateDataSource
    success_url = \
        "horizon:project:data_processing.jobs:create-data-source"
    classes = ("ajax-modal",)
    template_name = "data_sources/create.html"
    page_title = _("Create Data Source")


class EditDataSourceView(CreateDataSourceView):
    workflow_class = edit_flow.EditDataSource
    page_title = _("Edit Data Source")

    def get_context_data(self, **kwargs):
        context = super(EditDataSourceView, self) \
            .get_context_data(**kwargs)

        context["data_source_id"] = kwargs["data_source_id"]
        return context

    def get_initial(self):
        initial = super(EditDataSourceView, self).get_initial()
        initial['data_source_id'] = self.kwargs['data_source_id']
        return initial


class DataSourceDetailsView(tabs.TabView):
    tab_group_class = _tabs.DataSourceDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ data_source.name|default:data_source.id }}"

    @memoized.memoized_method
    def get_object(self):
        ds_id = self.kwargs["data_source_id"]
        try:
            return saharaclient.data_source_get(self.request, ds_id)
        except Exception:
            msg = _('Unable to retrieve details for data source "%s".') % ds_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(DataSourceDetailsView, self).get_context_data(**kwargs)
        data_source = self.get_object()
        context['data_source'] = data_source
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(data_source)
        return context

    def _get_actions(self, data_source):
        table = ds_tables.DataSourcesTable(self.request)
        return table.render_row_actions(data_source)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing.jobs:index")
