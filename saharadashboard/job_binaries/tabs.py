# Copyright (c) 2013 Red Hat Inc.
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
from horizon import tabs

from saharadashboard.api.client import client as saharaclient

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_binaries_details_tab"
    template_name = ("job_binaries/_details.html")

    def get_context_data(self, request):
        job_binary_id = self.tab_group.kwargs['job_binary_id']
        sahara = saharaclient(request)
        job_binary = sahara.job_binaries.get(job_binary_id)
        return {"job_binary": job_binary}


class JobBinaryDetailsTabs(tabs.TabGroup):
    slug = "job_binary_details"
    tabs = (GeneralTab,)
    sticky = True
