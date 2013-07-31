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
from horizon import workflows

from savannadashboard.api import client as savannaclient

from savannadashboard.job_origins.tables import JobOriginsTable
import savannadashboard.job_origins.tabs as _tabs
import savannadashboard.job_origins.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class JobOriginsView(tables.DataTableView):
    table_class = JobOriginsTable
    template_name = 'job_origins/job_origins.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        job_origins = savanna.job_origins.list()
        return job_origins


class CreateJobOriginView(workflows.WorkflowView):
    workflow_class = create_flow.CreateJobOrigin
    success_url = \
        "horizon:savanna:job-origins:create-job-origin"
    classes = ("ajax-modal")
    template_name = "job_origins/create.html"


class JobOriginDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobOriginDetailsTabs
    template_name = 'job_origins/details.html'

    def get_context_data(self, **kwargs):
        context = super(JobOriginDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass
