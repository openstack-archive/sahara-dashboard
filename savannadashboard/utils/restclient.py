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


from horizon.api.base import url_for
import logging
import requests

LOG = logging.getLogger(__name__)


def get_savanna_url(request):
    url = url_for(request, 'mapreduce')
    if url is None:
        url = "http://localhost:9000/v1.0"
    #LOG.warning("request: " + str(request))
    return url + "/" + request.user.tenant_id


def get_plugins(request):
    token = request.user.token.id
    resp = requests.get(get_savanna_url(request) + "/plugins",
                        headers={"x-auth-token": token})
    if resp.status_code == 200:
        raw_plugins = resp.json()["plugins"]
        plugins = []
        LOG.warning("bean: " + str(raw_plugins))
        for raw_plugin in raw_plugins:
            LOG.warning("bean: " + str(raw_plugin))
            bean = Bean("Plugin", **raw_plugin)
            plugins.append(bean)
            LOG.warning("bean: " + str(bean))
        return plugins
    else:
        return []


class Bean(object):
    def __init__(self, beanname, **kwargs):
        self.beanname = beanname
        self._info = kwargs

    def __getattr__(self, k):
        if k not in self.__dict__:
            return self._info.get(k)
        return self.__dict__[k]

    def __str__(self):
        return '%s %s' % (self.beanname, str(self._info))

    def __nonzero__(self):
        return len(self._info)
