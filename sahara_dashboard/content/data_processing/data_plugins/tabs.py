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

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.data_plugins \
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

    def _generate_context(self, plugin):
        if not plugin:
            return {'plugin': plugin}

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


class LabelsTab(tabs.Tab):
    name = _("Label details")
    slug = "label_details_tab"
    template_name = "data_plugins/_label_details.html"

    def _label_color(self, label):
        color = 'info'
        if label == 'deprecated':
            color = 'danger'
        elif label == 'stable':
            color = 'success'
        return color

    def get_context_data(self, request, **kwargs):
        plugin_id = self.tab_group.kwargs['plugin_id']
        plugin = None
        try:
            plugin = saharaclient.plugin_get(request, plugin_id)
        except Exception as e:
            LOG.error("Unable to get plugin with plugin_id %s (%s)" %
                      (plugin_id, str(e)))
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve plugin.'))

        labels = []
        for label, data in plugin.plugin_labels.items():
            labels.append(
                {'name': label,
                 'color': self._label_color(label),
                 'description': data.get('description', _("No description")),
                 'scope': _("Plugin"), 'status': data.get('status', False)})

        for version, version_data in plugin.version_labels.items():
            for label, data in version_data.items():
                labels.append(
                    {'name': label,
                     'color': self._label_color(label),
                     'description': data.get('description',
                                             _("No description")),
                     'scope': _("Plugin version %s") % version,
                     'status': data.get('status', False)})

        return {"labels": labels}


class PluginDetailsTabs(tabs.TabGroup):
    slug = "cluster_details"
    tabs = (DetailsTab, LabelsTab)
    sticky = True
