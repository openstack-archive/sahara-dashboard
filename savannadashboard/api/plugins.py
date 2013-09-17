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

import urllib

from savannadashboard.api import base


class Plugin(base.Resource):
    resource_name = 'Plugin'

    def __init__(self, manager, info):
        base.Resource.__init__(self, manager, info)

        # Horizon requires each object in table to have an id
        self.id = self.name


class PluginManager(base.ResourceManager):
    resource_class = Plugin

    def list(self):
        return self._list('/plugins', 'plugins')

    def get(self, plugin_name):
        return self._get('/plugins/%s' % plugin_name, 'plugin')

    def get_version_details(self, plugin_name, hadoop_version):
        return self._get('/plugins/%s/%s' % (plugin_name, hadoop_version),
                         'plugin')

    def convert_to_cluster_template(self, plugin_name, hadoop_version,
                                    template_name, filecontent):
        resp = self.api.client.post('/plugins/%s/%s/convert-config/%s' %
                                    (plugin_name,
                                     hadoop_version,
                                     urllib.quote(template_name)),
                                    filecontent)
        if resp.status_code != 202:
            raise RuntimeError('Failed to upload template file for plugin "%s"'
                               ' and version "%s"' %
                               (plugin_name, hadoop_version))
