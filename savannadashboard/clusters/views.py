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

from horizon import tables
from horizon import tabs
from horizon import workflows

from savannadashboard.api import client as savannaclient

from savannadashboard.clusters.tables import ClustersTable
import savannadashboard.clusters.tabs as _tabs
from savannadashboard.clusters.workflows import ConfigureCluster
from savannadashboard.clusters.workflows import CreateCluster


LOG = logging.getLogger(__name__)


class ClustersView(tables.DataTableView):
    table_class = ClustersTable
    template_name = 'clusters/clusters.html'

    def get_data(self):
        savanna = savannaclient.Client(self.request)
        clusters = savanna.clusters.list()
        return clusters


class ClusterDetailsView(tabs.TabView):
    tab_group_class = _tabs.ClusterDetailsTabs
    template_name = 'clusters/details.html'

    def get_context_data(self, **kwargs):
        context = super(ClusterDetailsView, self)\
            .get_context_data(**kwargs)
        return context

    def get_data(self):
        pass


class CreateClusterView(workflows.WorkflowView):
    workflow_class = CreateCluster
    success_url = \
        "horizon:savanna:clusters:create-cluster"
    classes = ("ajax-modal")
    template_name = "clusters/create.html"


class ConfigureClusterView(workflows.WorkflowView):
    workflow_class = ConfigureCluster
    success_url = "horizon:savanna:clusters"
    template_name = "clusters/configure.html"

    def get_context_data(self, **kwargs):
        context = super(ConfigureClusterView, self).get_context_data(
            **kwargs)

        context["plugin_name"] = self.request.session.get("plugin_name")
        context["plugin_version"] = self.request.session.get("plugin_version")

        return context
