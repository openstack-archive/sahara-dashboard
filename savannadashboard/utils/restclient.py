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
import json
import logging
import requests
from savannadashboard.utils.workflow_helpers import Parameter

LOG = logging.getLogger(__name__)


def get_savanna_url(request):
    url = url_for(request, 'mapreduce')
    if url is None:
        url = "http://localhost:9000/v1.0/" + request.user.tenant_id
    LOG.warning("request: " + str(request))
    return url


def get_plugins(request):
    token = request.user.token.id
    resp = requests.get(get_savanna_url(request) + "/plugins",
                        headers={"x-auth-token": token})
    if resp.status_code == 200:
        raw_plugins = resp.json()["plugins"]
        plugins = []
        for raw_plugin in raw_plugins:
            bean = Bean("Plugin", **raw_plugin)
            plugins.append(bean)
        return plugins
    else:
        return []


def get_general_node_configuration(request, plugin):
    #todo request
    return get_general_node_configuration_stub(plugin)


def get_general_node_configuration_stub(plugin):
    parameters = []
    if plugin == 'vanilla':
        parameters.append(Parameter("ulimit", "text", required=True))
        parameters.append(Parameter("something_else", "text", required=False))
    return parameters


def get_node_processes(request, plugin):
    #todo request
    return get_node_processes_stub(plugin)


def get_node_processes_stub(plugin):
    if plugin == 'vanilla':
        return [("name_node", "Name Node"),
                ("job_tracker", "Job Tracker"),
                ("data_node", "Data Node"),
                ("task_tracker", "Task Tracker")]


def get_configs_for_process(request, plugin, process):
    #todo request
    return get_configs_for_process_stub(plugin, process)


def get_node_processes_configs(request, plugin):
    processes = get_node_processes(request, plugin)
    configs = dict()
    for process, display_name in processes:
        configs[process] = get_configs_for_process(request, plugin, process)
    return configs


def get_configs_for_process_stub(plugin, process):
    if plugin == 'vanilla':
        if process == 'name_node':
            return [Parameter("heap_size", "text", required=True)]
        if process == 'data_node':
            return [Parameter("heap_size", "text", required=True)]
        elif process == 'job_tracker':
            return [Parameter("heap_size", "text", required=True),
                    Parameter("mapred.maxattempts", "text", required=False)]
        elif process == 'task_tracker':
            return [Parameter("heap_size", "text", required=True),
                    Parameter("mapred.maptasks", "text", required=False)]
    else:
        return []


def do_get_request(horizonRequest, url):
    token = horizonRequest.user.token.id
    return requests.get(get_savanna_url(horizonRequest) + url,
                        headers={"x-auth-token": token})


def do_post_request(horizonRequest, url, data):
    token = horizonRequest.user.token.id
    return requests.post(get_savanna_url(horizonRequest) + url, data,
                         headers={"x-auth-token": token,
                                  "content-type": "application/json"})


def get_images(request):
    resp = do_get_request(request, "/images")

    if resp.status_code == 200:
        raw_images = resp.json()["images"]
        images = []
        for raw_image in raw_images:
            images.append(Bean("Image", **raw_image))
        return images
    else:
        raise RuntimeError(
            "Savanna returned non-200 response on get images request: %s"
            % resp.status_code)


def get_image_by_id(request, image_id):
    resp = do_get_request(request, "/images/%s" % image_id)

    if resp.status_code == 200:
        return Bean("Image", **resp.json())
    else:
        raise RuntimeError(
            "Savanna returned non-200 response on get image request: %s"
            % resp.status_code)


def add_image_tags(request, image_id, tags):
    data = json.dumps({"tags": tags})
    resp = do_post_request(request, "/images/%s/tag" % image_id, data)

    if resp.status_code != 202:
        raise RuntimeError(
            "Savanna returned non-200 response on add image tags request: %s"
            % resp.status_code)


def remove_image_tags(request, image_id, tags):
    data = json.dumps({"tags": tags})
    resp = do_post_request(request, "/images/%s/untag" % image_id, data)

    if resp.status_code != 202:
        raise RuntimeError(
            "Savanna returned non-200 response on add image tags request: %s"
            % resp.status_code)


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
