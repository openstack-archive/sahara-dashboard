# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Mirantis Inc.
#
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
from django import template

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

LOG = logging.getLogger(__name__)


def render_versions(plugin):
    template_name = 'plugins/_versions_list.html'
    context = {"plugin": plugin}
    return template.loader.render_to_string(template_name, context)


class PluginsTable(tables.DataTable):
    title = tables.Column("title",
                          verbose_name=_("Plugin name"),
                          link=("horizon:savanna:plugins:details"))

    versions = tables.Column(render_versions,
                             verbose_name=_("Supported hadoop versions"))

    description = tables.Column("description",
                                verbose_name=_("Plugin description"))

    class Meta:
        name = "plugins"
        verbose_name = _("Plugins")
        table_actions = ()
        row_actions = ()
