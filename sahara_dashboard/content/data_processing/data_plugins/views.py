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

from horizon import exceptions
from horizon import tables
from horizon import tabs
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.data_plugins. \
    tables as p_tables
import sahara_dashboard.content.data_processing.data_plugins. \
    tabs as p_tabs
from sahara_dashboard.content.data_processing.data_plugins.workflows \
    import update


class PluginsView(tables.DataTableView):
    table_class = p_tables.PluginsTable
    template_name = 'data_plugins/plugins.html'
    page_title = _("Data Processing Plugins")

    def get_data(self):
        try:
            plugins = saharaclient.plugin_list(self.request)
        except Exception:
            plugins = []
            msg = _('Unable to retrieve data processing plugins.')
            exceptions.handle(self.request, msg)
        return plugins


class PluginDetailsView(tabs.TabView):
    tab_group_class = p_tabs.PluginDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = _("Data Processing Plugin Details")


class UpdatePluginView(workflows.WorkflowView):
    workflow_class = update.UpdatePlugin
    success_url = "horizon:project:data_processing.data_plugins"
    classes = ("ajax-modal",)
    template_name = "data_plugins/update.html"
    page_title = _("Update Plugin")

    def get_context_data(self, **kwargs):
        context = super(UpdatePluginView, self) \
            .get_context_data(**kwargs)
        context["plugin_name"] = kwargs["plugin_name"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            plugin_name = self.kwargs['plugin_name']
            try:
                plugin = saharaclient.plugin_get(self.request, plugin_name)
            except Exception:
                exceptions.handle(self.request,
                                  _("Unable to fetch plugin object."))
            self._object = plugin
        return self._object

    def get_initial(self):
        initial = super(UpdatePluginView, self).get_initial()
        initial['plugin_name'] = self.kwargs['plugin_name']
        return initial
