import savannadashboard.api.base as base


class NodeGroup(object):
    def __init__(self, name, node_group_template_id=None, flavor_id=None,
                 node_processes=None, node_configs=None, count=None):
        self.name = name
        self.node_group_template_id = node_group_template_id
        self.flavor_id = flavor_id
        self.node_processes = node_processes
        self.node_configs = node_configs
        self.count = count

    def _assert_field(self, field_name):
        if getattr(self, field_name) is None:
            raise base.APIException('Node group has no %s: %s' %
                                    (field_name, str(self)))

    def _copy_if_defined(self, data, field_name):
        if getattr(self, field_name) is not None:
            data[field_name] = getattr(self, field_name)

    def as_dict(self):
        self._assert_field('name')
        self._assert_field('count')

        data = {
            'name': self.name,
            'count': self.count
        }

        if self.node_group_template_id is None:
            self._assert_field('flavor_id')
            self._assert_field('node_processes')
            self._assert_field('node_configs')

        self._copy_if_defined(data, 'node_group_template_id')
        self._copy_if_defined(data, 'flavor_id')
        self._copy_if_defined(data, 'node_processes')
        self._copy_if_defined(data, 'node_configs')

        return data

    def __str__(self):
        return '(Node Group %s)' % self.__dict__
