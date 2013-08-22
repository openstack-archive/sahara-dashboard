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

from savannadashboard.data_sources.tables import DataSourcesTable
import savannadashboard.data_sources.tabs as _tabs
import savannadashboard.data_sources.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class DataSourcesView(tables.DataTableView):
    table_class = DataSourcesTable
    template_name = 'data_sources/data_sources.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        data_sources = savanna.data_sources.list()
        return data_sources

    class FakeDataSource(object):
        pass


class CreateDataSourceView(workflows.WorkflowView):
    workflow_class = create_flow.CreateDataSource
    success_url = \
        "horizon:savanna:data-sources:create-data-source"
    classes = ("ajax-modal")
    template_name = "data_sources/create.html"


class DataSourceDetailsView(tabs.TabView):
    tab_group_class = _tabs.DataSourceDetailsTabs
    template_name = 'data_sources/details.html'

    def get_context_data(self, **kwargs):
        context = super(DataSourceDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass
