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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.clusters. \
    nodegroup_templates.workflows.create as create_flow


class CopyNodegroupTemplate(create_flow.ConfigureNodegroupTemplate):
    success_message = _("Node Group Template copy %s created")

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        self.template_id = context_seed["template_id"]
        self.template = saharaclient.nodegroup_template_get(request,
                                                            self.template_id)
        self._set_configs_to_copy(self.template.node_configs)

        plugin = self.template.plugin_name
        if saharaclient.VERSIONS.active == '2':
            version_attr = 'plugin_version'
        else:
            version_attr = 'hadoop_version'
        hadoop_version = getattr(self.template, version_attr)

        request.GET = request.GET.copy()
        request.GET.update(
            {"plugin_name": plugin, version_attr: hadoop_version})

        super(CopyNodegroupTemplate, self).__init__(request, context_seed,
                                                    entry_point, *args,
                                                    **kwargs)

        g_fields = None
        snp_fields = None
        s_fields = None
        share_fields = None
        for step in self.steps:
            if isinstance(step, create_flow.GeneralConfig):
                g_fields = step.action.fields
            if isinstance(step, create_flow.SecurityConfig):
                s_fields = step.action.fields
            if isinstance(step, create_flow.SelectNodeProcesses):
                snp_fields = step.action.fields
            if isinstance(step, create_flow.SelectNodeGroupShares):
                share_fields = step.action.fields

        g_fields["nodegroup_name"].initial = self.template.name + "-copy"
        g_fields["description"].initial = self.template.description
        g_fields["flavor"].initial = self.template.flavor_id

        if hasattr(self.template, "availability_zone"):
            g_fields["availability_zone"].initial = (
                self.template.availability_zone)

        if hasattr(self.template, "volumes_availability_zone"):
            g_fields["volumes_availability_zone"].initial = \
                self.template.volumes_availability_zone

        storage = "cinder_volume" if self.template.volumes_per_node > 0 \
            else "ephemeral_drive"
        volumes_per_node = self.template.volumes_per_node
        volumes_size = self.template.volumes_size
        volume_type = self.template.volume_type
        volume_local_to_instance = self.template.volume_local_to_instance
        g_fields["storage"].initial = storage
        g_fields["volumes_per_node"].initial = volumes_per_node
        g_fields["volumes_size"].initial = volumes_size
        g_fields["volumes_availability_zone"].initial = \
            self.template.volumes_availability_zone
        g_fields['volume_type'].initial = volume_type
        g_fields['volume_local_to_instance'].initial = volume_local_to_instance
        g_fields["proxygateway"].initial = self.template.is_proxy_gateway
        g_fields["use_autoconfig"].initial = self.template.use_autoconfig
        g_fields["is_public"].initial = self.template.is_public
        g_fields['is_protected'].initial = self.template.is_protected
        g_fields["image"].initial = self.template.image_id

        if self.template.floating_ip_pool:
            g_fields['floating_ip_pool'].initial = (
                self.template.floating_ip_pool)

        s_fields["security_autogroup"].initial = (
            self.template.auto_security_group)

        if self.template.security_groups:
            s_fields["security_groups"].initial = dict(
                [(sg, sg) for sg in self.template.security_groups])

        processes_dict = dict()
        try:
            plugin_details = saharaclient.plugin_get_version_details(
                request,
                plugin,
                hadoop_version)
            plugin_node_processes = plugin_details.node_processes
        except Exception:
            plugin_node_processes = dict()
            exceptions.handle(request,
                              _("Unable to fetch plugin details."))
        for process in self.template.node_processes:
            # need to know the service
            _service = None
            for service, processes in plugin_node_processes.items():
                if process in processes:
                    _service = service
                    break
            processes_dict["%s:%s" % (_service, process)] = process
        snp_fields["processes"].initial = processes_dict

        if share_fields:
            share_fields["shares"].initial = (
                self._get_share_defaults(share_fields))

    def _get_share_defaults(self, share_fields):
        values = dict()
        choices = share_fields['shares'].choices
        for i, choice in enumerate(choices):
            share_id = choice[0]
            s = [s for s in self.template.shares if s['id'] == share_id]
            if len(s) > 0:
                path = s[0].get('path', '')
                values["share_id_{0}".format(i)] = {
                    "id": s[0]["id"],
                    "path": path,
                    "access_level": s[0]["access_level"]
                }
            else:
                values["share_id_{0}".format(i)] = {
                    "id": None,
                    "path": None,
                    "access_level": None
                }
        return values
