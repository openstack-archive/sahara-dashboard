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

import logging

from django.utils.translation import ugettext as _

from savannadashboard.api.client import client as savannaclient
import savannadashboard.nodegroup_templates.workflows.create as create_flow

LOG = logging.getLogger(__name__)


class CopyNodegroupTemplate(create_flow.ConfigureNodegroupTemplate):
    success_message = _("Node Group Template copy %s created")

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        savanna = savannaclient(request)

        template_id = context_seed["template_id"]
        template = savanna.node_group_templates.get(template_id)
        self._set_configs_to_copy(template.node_configs)

        plugin = template.plugin_name
        hadoop_version = template.hadoop_version

        request.GET = request.GET.copy()
        request.GET.update({"plugin_name": plugin})
        request.GET.update({"hadoop_version": hadoop_version})

        super(CopyNodegroupTemplate, self).__init__(request, context_seed,
                                                    entry_point, *args,
                                                    **kwargs)

        for step in self.steps:
            if not isinstance(step, create_flow.GeneralConfig):
                continue
            fields = step.action.fields

            fields["nodegroup_name"].initial = template.name + "-copy"
            fields["description"].initial = template.description
            fields["flavor"].initial = template.flavor_id

            storage = "cinder_volume" if template.volumes_per_node > 0 \
                else "ephemeral_drive"
            volumes_per_node = template.volumes_per_node
            volumes_size = template.volumes_size
            fields["storage"].initial = storage
            fields["volumes_per_node"].initial = volumes_per_node
            fields["volumes_size"].initial = volumes_size

            processes_dict = dict()
            plugin_details = savanna.plugins.get_version_details(
                plugin,
                hadoop_version)
            plugin_node_processes = plugin_details.node_processes
            for process in template.node_processes:
                #need to know the service
                _service = None
                for service, processes in plugin_node_processes.items():
                    if process in processes:
                        _service = service
                        break
                processes_dict.update({"%s:%s" % (_service, process): process})
            fields["processes"].initial = processes_dict
