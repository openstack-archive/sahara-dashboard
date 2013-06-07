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

from horizon import exceptions
from horizon import forms
from horizon import workflows

from horizon.api import glance
from horizon.api import nova

from django.utils.translation import ugettext as _

import savannadashboard.api.api_objects as api_objects
from savannadashboard.api import client as savannaclient
import savannadashboard.cluster_templates.workflows as t_flows

import logging

LOG = logging.getLogger(__name__)


class SelectPluginAction(t_flows.SelectPluginAction):
    class Meta:
        name = _("Select plugin and hadoop version for cluster")
        help_text_template = ("clusters/_create_general_help.html")


class SelectPlugin(t_flows.SelectPlugin):
    pass


class CreateCluster(t_flows.CreateClusterTemplate):
    slug = "create_cluster"
    name = _("Create Cluster")
    success_url = "horizon:savanna:cluster_templates:index"

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        request.session["groups_count"] = 0
        super(CreateCluster, self).__init__(request,
                                            context_seed,
                                            entry_point,
                                            *args, **kwargs)


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

    def populate_image_choices(self, request, context):
        public_images, _more = glance.image_list_detailed(request)
        return [(image.id, image.name) for image in public_images]

    def populate_keypair_choices(self, request, context):
        keypairs = nova.keypair_list(request)
        keypair_list = [(kp.name, kp.name) for kp in keypairs]
        return keypair_list

    def populate_cluster_template_choices(selfs, request, context):
        savanna = savannaclient.Client(request)
        templates = savanna.cluster_templates.list()
        plugin_name = request.session["plugin_name"]
        hadoop_version = request.session["hadoop_version"]

        choices = [(template.id, template.name)
                   for template in templates
                   if (template.hadoop_version == hadoop_version and
                       template.plugin_name == plugin_name)]

        return choices

    def get_help_text(self):
        extra = dict()
        extra["plugin_name"] = self.request.session.get("plugin_name")
        extra["hadoop_version"] = self.request.session.get("hadoop_version")
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
            ("cluster_templates/_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v
        return context


class ConfigureClusterAction(workflows.Action):
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))

    def __init__(self, request, *args, **kwargs):
        super(ConfigureClusterAction, self).\
            __init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        all_templates = savanna.node_group_templates.list()
        templates = [
            (template.id, template.name)
            for template in all_templates
            if (template.plugin_name == request.session.get("plugin_name")
                and template.hadoop_version ==
                request.session.get("hadoop_version"))
        ]

        count = int(request.session.get("groups_count", 0))
        skip_values = request.session.get("ignore_idxs", [])
        for dictionary in args:
            if dictionary.get("general_hidden_configure_field", None) \
                    == "create_nodegroup":
                count += 1
                request.session["groups_count"] = count
                #break
            if dictionary.get("general_hidden_to_delete_field", None):
                current_ignored = request.session.get("ignore_idxs", [])
                new_ignored = [int(idx)
                               for idx in
                               dictionary["general_hidden_to_delete_field"]
                               .split(",") if idx]
                current_ignored += new_ignored
                skip_values = current_ignored
                request.session["ignore_idxs"] = current_ignored

        for idx in range(0, count, 1):
            if idx in skip_values:
                continue

            self.fields["group_name_" + str(idx)] = forms.CharField(
                label=_("Name"),
                required=True,
                widget=forms.TextInput(
                    attrs={"class": "name-field",
                           "data-name-idx": str(idx)}))

            self.fields["group_template_" + str(idx)] = forms.ChoiceField(
                label=_("Node group template"),
                required=True,
                choices=templates,
                widget=forms.Select(
                    attrs={"class": "ng-field",
                           "data-ng-idx": str(idx)}))

            self.fields["group_count_" + str(idx)] = forms.IntegerField(
                label=_("Count"),
                required=True,
                min_value=1,
                widget=forms.TextInput(
                    attrs={"class": "count-field",
                           "data-count-idx": str(idx)})
            )

    def clean(self):
        cleaned_data = super(ConfigureClusterAction, self).clean()
        if cleaned_data.get("hidden_nodegroups_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta:
        name = _("Cluster Node groups")


class ConfigureClusterStep(workflows.Step):
    action_class = ConfigureClusterAction
    contributes = ("hidden_nodegroups_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["ng_" + k] = v
        return context


class ConfigureCluster(workflows.Workflow):
    slug = "configure_cluster"
    name = _("Create Cluster")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:clusters:index"
    default_steps = (GeneralConfig, ConfigureClusterStep)

    def is_valid(self):
        if self.context["general_hidden_configure_field"] \
                == "create_nodegroup":
            return False
        missing = self.depends_on - set(self.context.keys())
        if missing:
            raise exceptions.WorkflowValidationError(
                "Unable to complete the workflow. The values %s are "
                "required but not present." % ", ".join(missing))

        steps_valid = True
        for step in self.steps:
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            savanna = savannaclient.Client(request)
            node_groups = []
            ng_names = {}
            ng_templates = {}
            ng_counts = {}
            for key, val in context.items():
                if str(key).startswith("ng_"):
                    if str(key).startswith("ng_group_name_"):
                        idx = str(key)[len("ng_group_name_"):]
                        ng_names[idx] = val
                    elif str(key).startswith("ng_group_template_"):
                        idx = str(key)[len("ng_group_template_"):]
                        ng_templates[idx] = val
                    elif str(key).startswith("ng_group_count_"):
                        idx = str(key)[len("ng_group_count_"):]
                        ng_counts[idx] = val
            for key, val in ng_names.items():
                ng = api_objects.NodeGroup(val,
                                           ng_templates[key],
                                           count=ng_counts[key])
                node_groups.append(ng)

            savanna.clusters.create(context["general_cluster_name"],
                                    request.session.get("plugin_name"),
                                    request.session.get("hadoop_version"),
                                    context["general_cluster_template"],
                                    context["general_image"],
                                    context["general_description"],
                                    node_groups,
                                    context["general_keypair"]
                                    )
            return True
        except Exception:
            exceptions.handle(request)
            return False
