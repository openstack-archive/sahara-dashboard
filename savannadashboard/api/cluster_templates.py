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
