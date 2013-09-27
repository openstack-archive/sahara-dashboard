# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from horizon import tables
from horizon import tabs

from savannadashboard.api.client import client as savannaclient

from savannadashboard.job_executions.tables import JobExecutionsTable
import savannadashboard.job_executions.tabs as _tabs

LOG = logging.getLogger(__name__)


class JobExecutionsView(tables.DataTableView):
    table_class = JobExecutionsTable
    template_name = 'job_executions/job_executions.html'

    def get_data(self):
        savanna = savannaclient(self.request)
        jobs = savanna.job_executions.list()
        return jobs


class JobExecutionDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobExecutionDetailsTabs
    template_name = 'job_executions/details.html'

    def get_context_data(self, **kwargs):
        context = super(JobExecutionDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass
