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

from saharadashboard.api.client import client as saharaclient

from saharadashboard.clusters.tables import ClustersTable
import saharadashboard.clusters.tabs as _tabs
import saharadashboard.clusters.workflows.create as create_flow
import saharadashboard.clusters.workflows.scale as scale_flow

LOG = logging.getLogger(__name__)


class ClustersView(tables.DataTableView):
    table_class = ClustersTable
    template_name = 'clusters/clusters.html'

    def get_data(self):
        sahara = saharaclient(self.request)
        clusters = sahara.clusters.list()
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
    workflow_class = create_flow.CreateCluster
    success_url = \
        "horizon:sahara:clusters:create-cluster"
    classes = ("ajax-modal")
    template_name = "clusters/create.html"


class ConfigureClusterView(workflows.WorkflowView):
    workflow_class = create_flow.ConfigureCluster
    success_url = "horizon:sahara:clusters"
    template_name = "clusters/configure.html"


class ScaleClusterView(workflows.WorkflowView):
    workflow_class = scale_flow.ScaleCluster
    success_url = "horizon:sahara:clusters"
    classes = ("ajax-modal")
    template_name = "clusters/scale.html"

    def get_context_data(self, **kwargs):
        context = super(ScaleClusterView, self)\
            .get_context_data(**kwargs)

        context["cluster_id"] = kwargs["cluster_id"]
        return context

    def get_object(self, *args, **kwargs):
        if not hasattr(self, "_object"):
            template_id = self.kwargs['cluster_id']
            sahara = saharaclient(self.request)
            template = sahara.cluster_templates.get(template_id)
            self._object = template
        return self._object

    def get_initial(self):
        initial = super(ScaleClusterView, self).get_initial()
        initial.update({'cluster_id': self.kwargs['cluster_id']})
        return initial
