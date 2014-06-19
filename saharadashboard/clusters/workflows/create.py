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

from horizon import exceptions
from horizon import forms
from horizon import workflows

from saharadashboard.utils import importutils
from saharadashboard.utils import neutron_support
import saharadashboard.utils.workflow_helpers as whelpers

neutron = importutils.import_any('openstack_dashboard.api.quantum',
                                 'openstack_dashboard.api.neutron',
                                 'horizon.api.quantum',
                                 'horizon.api.neutron')

nova = importutils.import_any('openstack_dashboard.api.nova',
                              'horizon.api.nova')

from django.utils.translation import ugettext as _

from saharaclient.api import base as api_base
from saharadashboard.api import client as saharaclient
from saharadashboard.api.client import SAHARA_USE_NEUTRON
import saharadashboard.cluster_templates.workflows.create as t_flows

import logging

LOG = logging.getLogger(__name__)


class SelectPluginAction(t_flows.SelectPluginAction):
    class Meta:
        name = _("Select plugin and hadoop version for cluster")
        help_text_template = ("clusters/_create_general_help.html")


class SelectPlugin(t_flows.SelectPlugin):
    action_class = SelectPluginAction


class CreateCluster(t_flows.CreateClusterTemplate):
    slug = "create_cluster"
    name = _("Launch Cluster")
    success_url = "horizon:sahara:cluster_templates:index"
    default_steps = (SelectPlugin,)


class GeneralConfigAction(workflows.Action):
    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    hidden_to_delete_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_to_delete_field"}))

    cluster_name = forms.CharField(label=_("Cluster Name"),
                                   required=True)

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea)
    cluster_template = forms.ChoiceField(label=_("Cluster Template"),
                                         initial=(None, "None"),
                                         required=False)

    image = forms.ChoiceField(label=_("Base Image"),
                              required=True)

    keypair = forms.ChoiceField(
        label=_("Keypair"),
        required=False,
        help_text=_("Which keypair to use for authentication."))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)

        if SAHARA_USE_NEUTRON:
            self.fields["neutron_management_network"] = forms.ChoiceField(
                label=_("Neutron Management Network"),
                required=True,
                choices=self.populate_neutron_management_network_choices(
                    request, {})
            )

        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin
        )
        self.fields["hadoop_version"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=hadoop_version
        )

    def populate_image_choices(self, request, context):
        sahara = saharaclient.client(request)
        all_images = sahara.images.list()

        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)

        details = sahara.plugins.get_version_details(plugin,
                                                     hadoop_version)

        return [(image.id, image.name) for image in all_images
                if set(details.required_image_tags).issubset(set(image.tags))]

    def populate_keypair_choices(self, request, context):
        keypairs = nova.keypair_list(request)
        keypair_list = [(kp.name, kp.name) for kp in keypairs]
        keypair_list.insert(0, ("", "No keypair"))
        return keypair_list

    def populate_cluster_template_choices(self, request, context):
        sahara = saharaclient.client(request)
        templates = sahara.cluster_templates.list()

        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(request)

        choices = [(template.id, template.name)
                   for template in templates
                   if (template.hadoop_version == hadoop_version and
                       template.plugin_name == plugin)]

        # cluster_template_id comes from cluster templates table, when
        # Create Cluster from template is clicked there
        selected_template_id = request.REQUEST.get("cluster_template_id", None)

        for template in templates:
            if template.id == selected_template_id:
                self.fields['cluster_template'].initial = template.id

        return choices

    populate_neutron_management_network_choices = \
        neutron_support.populate_neutron_management_network_choices

    def get_help_text(self):
        extra = dict()
        plugin, hadoop_version = whelpers.\
            get_plugin_and_hadoop_version(self.request)
        extra["plugin_name"] = plugin
        extra["hadoop_version"] = hadoop_version
        return super(GeneralConfigAction, self).get_help_text(extra)

    def clean(self):
        cleaned_data = super(GeneralConfigAction, self).clean()
        if cleaned_data.get("hidden_configure_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta:
        name = _("Configure Cluster")
        help_text_template = \
            ("clusters/_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        return context


class ConfigureCluster(whelpers.StatusFormatMixin, workflows.Workflow):
    slug = "configure_cluster"
    name = _("Launch Cluster")
    finalize_button_name = _("Create")
    success_message = _("Created Cluster %s")
    name_property = "general_cluster_name"
    success_url = "horizon:sahara:clusters:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        try:
            sahara = saharaclient.client(request)
            #TODO(nkonovalov) Implement AJAX Node Groups
            node_groups = None

            plugin, hadoop_version = whelpers.\
                get_plugin_and_hadoop_version(request)

            cluster_template_id = context["general_cluster_template"] or None
            user_keypair = context["general_keypair"] or None

            sahara.clusters.create(
                context["general_cluster_name"],
                plugin, hadoop_version,
                cluster_template_id=cluster_template_id,
                default_image_id=context["general_image"],
                description=context["general_description"],
                node_groups=node_groups,
                user_keypair_id=user_keypair,
                net_id=context.get("general_neutron_management_network", None))
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request)
