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

from savannadashboard.api import base


class ClusterTemplate(base.Resource):
    resource_name = 'Cluster Template'


class ClusterTemplateManager(base.ResourceManager):
    resource_class = ClusterTemplate

    def create(self, name, plugin_name, hadoop_version, description,
               cluster_configs, node_groups):

        # expecting node groups to be api_objects.NodeGroup
        data = {
            'name': name,
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'description': description,
            'cluster_configs': cluster_configs,
            'node_groups': [ng.as_dict() for ng in node_groups]
        }

        self._create('/cluster-templates', data)

    def list(self):
        return self._list('/cluster-templates', 'cluster_templates')

    def get(self, cluster_template_id):
        return self._get('/cluster-templates/%s' % cluster_template_id,
                         'cluster_template')

    def delete(self, cluster_template_id):
        self._delete('/cluster-templates/%s' % cluster_template_id)
