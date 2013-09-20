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

from savannadashboard.jobs.tables import JobsTable
import savannadashboard.jobs.tabs as _tabs
import savannadashboard.jobs.workflows.create as create_flow
import savannadashboard.jobs.workflows.launch as launch_flow

LOG = logging.getLogger(__name__)


class JobsView(tables.DataTableView):
    table_class = JobsTable
    template_name = 'jobs/jobs.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        jobs = savanna.jobs.list()
        return jobs


class CreateJobView(workflows.WorkflowView):
    workflow_class = create_flow.CreateJob
    success_url = \
        "horizon:savanna:jobs:create-job"
    classes = ("ajax-modal")
    template_name = "jobs/create.html"


class JobDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobDetailsTabs
    template_name = 'jobs/details.html'

    def get_context_data(self, **kwargs):
        context = super(JobDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class LaunchJobView(workflows.WorkflowView):
    workflow_class = launch_flow.LaunchJob
    success_url = \
        "horizon:savanna:jobs"
    classes = ("ajax-modal")
    template_name = "jobs/launch.html"

    def get_context_data(self, **kwargs):
        context = super(LaunchJobView, self)\
            .get_context_data(**kwargs)
        return context
