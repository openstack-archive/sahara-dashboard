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

from django.utils.translation import ugettext as _
import horizon

from saharadashboard.utils import compatibility

LOG = logging.getLogger(__name__)


class SaharaDashboard(horizon.Dashboard):
    name = _("Sahara")
    slug = "sahara"
    panels = ('clusters',
              'cluster_templates',
              'nodegroup_templates',
              'job_executions',
              'jobs',
              'job_binaries',
              'data_sources',
              'image_registry',
              'plugins')
    default_panel = 'clusters'
    nav = True
    supports_tenants = True


horizon.register(SaharaDashboard)

LOG.info('Sahara recognizes Dashboard release as "%s"' %
         compatibility.get_dashboard_release())
