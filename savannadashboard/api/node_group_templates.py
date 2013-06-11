from savannadashboard.api import base


class NodeGroupTemplate(base.Resource):
    resource_name = 'Node Group Template'


class NodeGroupTemplateManager(base.ResourceManager):
    resource_class = NodeGroupTemplate

    def create(self, name, plugin_name, hadoop_version, description, flavor_id,
               node_processes, node_configs):

        data = {
            'name': name,
            'plugin_name': plugin_name,
            'hadoop_version': hadoop_version,
            'description': description,
            'flavor_id': flavor_id,
            'node_processes': node_processes,
            'node_configs': node_configs
        }

        self._create('/node-group-templates', data)

    def list(self):
        return self._list('/node-group-templates', 'node_group_templates')

    def get(self, ng_template_id):
        return self._get('/node-group-templates/%s' % ng_template_id,
                         'node_group_template')

    def delete(self, ng_template_id):
        self._delete('/node-group-templates/%s' % ng_template_id)
