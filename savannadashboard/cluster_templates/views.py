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


from horizon import tables
import logging

from savannadashboard.cluster_templates.tables import ClusterTemplatesTable

LOG = logging.getLogger(__name__)


class ClusterTemplatesView(tables.DataTableView):
    table_class = ClusterTemplatesTable
    template_name = 'cluster_templates/cluster_templates.html'

    def get_data(self):
        #todo get data from client
        cluster_templates = []
        return cluster_templates
