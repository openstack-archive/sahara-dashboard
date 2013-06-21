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
