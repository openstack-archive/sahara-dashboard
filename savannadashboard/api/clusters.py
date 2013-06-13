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
               cluster_configs=None, node_groups=None, user_keypair_id=None):

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
                              default_image_id=default_image_id,
                              cluster_configs=cluster_configs,
                              node_groups=node_groups,
                              user_keypair_id=user_keypair_id)

        self._create('/clusters', data)

    def list(self):
        return self._list('/clusters', 'clusters')

    def get(self, cluster_id):
        return self._get('/clusters/%s' % cluster_id, 'cluster')

    def delete(self, cluster_id):
        self._delete('/clusters/%s' % cluster_id)
