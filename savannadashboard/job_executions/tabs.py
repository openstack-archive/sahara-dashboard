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

from savannadashboard.api.client import client as savannaclient

LOG = logging.getLogger(__name__)


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_execution_tab"
    template_name = ("job_executions/_details.html")

    def get_context_data(self, request):
        job_execution_id = self.tab_group.kwargs['job_execution_id']
        savanna = savannaclient(request)
        job_execution = savanna.job_executions.get(job_execution_id)
        return {"job_execution": job_execution}


class JobExecutionDetailsTabs(tabs.TabGroup):
    slug = "job_execution_details"
    tabs = (GeneralTab,)
    sticky = True
