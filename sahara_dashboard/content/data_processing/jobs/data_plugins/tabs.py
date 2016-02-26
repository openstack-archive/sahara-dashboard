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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.jobs.data_plugins \
    import tables as plugin_tables
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs

LOG = logging.getLogger(__name__)


class PluginsTab(sahara_tabs.SaharaTableTab):
    table_classes = (plugin_tables.PluginsTable, )
    name = _("Plugins")
    slug = "plugins_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_plugins_data(self):
        try:
            plugins = saharaclient.plugin_list(self.request)
        except Exception:
            plugins = []
            exceptions.handle(self.request,
                              _("Unable to fetch plugin list"))
        return plugins


class DetailsTab(tabs.Tab):
    name = _("Details")
    slug = "plugin_details_tab"
    template_name = "data_plugins/_details.html"

    def get_context_data(self, request):
        plugin_id = self.tab_group.kwargs['plugin_id']
        plugin = None
        try:
            plugin = saharaclient.plugin_get(request, plugin_id)
        except Exception as e:
            LOG.error("Unable to get plugin with plugin_id %s (%s)" %
                      (plugin_id, str(e)))
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve plugin.'))
        return {"plugin": plugin}


class PluginDetailsTabs(tabs.TabGroup):
    slug = "cluster_details"
    tabs = (DetailsTab,)
    sticky = True
