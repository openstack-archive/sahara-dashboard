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

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.jobs. \
    data_plugins.tables as p_tables
import sahara_dashboard.content.data_processing.jobs. \
    data_plugins.tabs as p_tabs


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
