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

from django.template import loader
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from sahara_dashboard.content.data_processing.utils \
    import workflow_helpers as w_helpers


class UpdatePluginAction(tables.LinkAction):
    name = "update_plugin"
    verbose_name = _("Update Plugin")
    url = "horizon:project:data_processing.data_plugins:update"
    classes = ("ajax-modal", "btn-edit")


def versions_to_string(plugin):
    template_name = 'data_plugins/_list_versions.html'
    versions = w_helpers.get_enabled_versions(plugin)
    context = {"versions": versions}
    return loader.render_to_string(template_name, context)


class PluginsTable(tables.DataTable):
    title = tables.Column("title",
                          verbose_name=_("Title"),
                          link=("horizon:project:data_processing."
                                "data_plugins:plugin-details"))

    versions = tables.Column(versions_to_string,
                             verbose_name=_("Enabled Versions"))

    description = tables.Column("description",
                                verbose_name=_("Description"))

    class Meta(object):
        name = "plugins"
        verbose_name = _("Plugins")

        row_actions = (UpdatePluginAction,)
