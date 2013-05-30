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
from savannadashboard.clusters.tables import ClustersTable

LOG = logging.getLogger(__name__)


class ClustersView(tables.DataTableView):
    table_class = ClustersTable
    template_name = 'clusters/clusters.html'

    def get_data(self):
        #todo get data from client
        clusters = []
        return clusters
