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

import logging

from django.utils.translation import ugettext_lazy as _

from horizon import tables

LOG = logging.getLogger(__name__)


class CreateNodegroupTemplate(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Node group Template")
    url = "horizon:savanna:nodegroup_templates:create-nodegroup-template"
    classes = ("ajax-modal", "btn-create", "create-nodegrouptemplate-btn")


class ConfigureNodegroupTemplate(tables.LinkAction):
    name = "configure"
    verbose_name = _("Configure Node group Template")
    url = "horizon:savanna:nodegroup_templates:configure-nodegroup-template"
    classes = ("ajax-modal", "btn-create", "configure-nodegrouptemplate-btn")


class NodegroupTemplatesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Node group template name"),
                         link=("horizon:savannadashboard:nodegroup_templates:"
                               "nodegroup_template_details"))

    class Meta:
        name = "nodegroup_templates"
        verbose_name = _("Node group Templates")
        table_actions = (CreateNodegroupTemplate, ConfigureNodegroupTemplate)
        row_actions = ()
