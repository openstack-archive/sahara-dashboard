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


class Cluster(base.Resource):
    resource_name = 'Cluster'


class ClusterManager(base.ResourceManager):
    resource_class = Cluster

    def _assert_variables(self, **kwargs):
        for var_name, var_value in kwargs.iteritems():
            if var_value is None:
                raise base.APIException('Cluster is missing field "%s"' %
                                        var_name)

    def _copy_if_defined(self, data, **kwargs):
        for var_name, var_value in kwargs.iteritems():
            if var_value is not None:
                data[var_name] = var_value

    def create(self, name, plugin_name, hadoop_version,
               cluster_template_id=None, default_image_id=None,
               description=None, cluster_configs=None, node_groups=None,
               user_keypair_id=None, anti_affinity=None, net_id=None):

        # expecting node groups to be api_objects.NodeGroup
        if node_groups is not None:
            node_groups = [ng.as_dict() for ng in node_groups]

        data = {
            'name': name,
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
        }

        if cluster_template_id is None:
            self._assert_variables(default_image_id=default_image_id,
                                   cluster_configs=cluster_configs,
                                   node_groups=node_groups)

        self._copy_if_defined(data,
                              cluster_template_id=cluster_template_id,
                              default_image_id=default_image_id,
                              description=description,
                              cluster_configs=cluster_configs,
                              node_groups=node_groups,
                              user_keypair_id=user_keypair_id,
                              anti_affinity=anti_affinity,
                              neutron_management_network=net_id)

        self._create('/clusters', data)

    def scale(self, cluster_id, scale_object):
        return self._update('/clusters/%s' % cluster_id, scale_object)

    def list(self):
        return self._list('/clusters', 'clusters')

    def get(self, cluster_id):
        return self._get('/clusters/%s' % cluster_id, 'cluster')

    def delete(self, cluster_id):
        self._delete('/clusters/%s' % cluster_id)
