
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

from horizon.api import glance
from horizon.api import nova
import logging

from horizon import exceptions
from horizon import forms
from horizon import workflows

from django.utils.translation import ugettext as _
from savannadashboard.utils.restclient import get_plugins

LOG = logging.getLogger(__name__)


class SelectPluginAction(workflows.Action):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        plugins = get_plugins(request)
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin name"),
            required=True,
            choices=plugin_choices,
            widget=forms.Select(attrs={"class": "plugin_name_choice"}))

        for plugin in plugins:
            field_name = plugin.name + "_version"
            choice_field = forms.ChoiceField(
                label=_("Hadoop version"),
                required=True,
                choices=[(version, version) for version in plugin.versions],
                widget=forms.Select(
                    attrs={"class": "plugin_version_choice "
                                    + field_name + "_choice"})
            )
            self.fields[field_name] = choice_field

    class Meta:
        name = _("Select plugin and hadoop version for cluster template")
        help_text_template = ("cluster_templates/_create_general_help.html")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction
    contributes = ("plugin_name", "hadoop_version")

    def contribute(self, data, context):
        context = super(SelectPlugin, self).contribute(data, context)
        context["plugin_name"] = data.get('plugin_name', None)
        context["hadoop_version"] = \
            data.get(context["plugin_name"] + "_version", None)
        return context


class CreateClusterTemplate(workflows.Workflow):
    slug = "create_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:cluster_templates:index"
    default_steps = (SelectPlugin,)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        request.session["groups_count"] = 0
        super(CreateClusterTemplate, self).__init__(request,
                                                    context_seed,
                                                    entry_point,
                                                    *args, **kwargs)

    def handle(self, request, context):
        try:
            request.session["plugin_name"] = context["plugin_name"]
            request.session["hadoop_version"] = context["hadoop_version"]
            return True
        except Exception:
            exceptions.handle(request)
            return False


class GeneralConfigAction(workflows.Action):
    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    cluster_name = forms.CharField(label=_("Template Name"),
                                   required=True)

    base_image = forms.ChoiceField(label=_("Base Image"),
                                   required=True)

    separate_machines = forms.BooleanField(
        label=_("Run data nodes on separate machines"),
        required=False)

    keypair = forms.ChoiceField(
        label=_("Keypair"),
        required=False,
        help_text=_("Which keypair to use for authentication."))

    hdfs_placement = forms.ChoiceField(
        label=_("HDFS Data Node storage location"),
        required=True,
        help_text=_("Which keypair to use for authentication."),
        choices=[("ephemeral_drive", "Ephemeral Drive"),
                 ("cinder_volume", "Cinder Volume")])

    def populate_base_image_choices(self, request, context):
        public_images, _more = glance.image_list_detailed(request)
        return [(image.id, image.name) for image in public_images]

    def populate_keypair_choices(self, request, context):
        keypairs = nova.keypair_list(request)
        keypair_list = [(kp.name, kp.name) for kp in keypairs]
        return keypair_list

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
        name = _("Configure Cluster Template")
        help_text_template = \
            ("cluster_templates/_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v
        return context


class ConfigureNodegroupsAction(workflows.Action):
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))

    def __init__(self, request, *args, **kwargs):
        super(ConfigureNodegroupsAction, self).\
            __init__(request, *args, **kwargs)

        #todo get templates form api
        #plugin = request.session.get("plugin_name")
        templates = []

        count = int(request.session.get("groups_count", 0))

        for dictionary in args:
            if dictionary.get("general_hidden_configure_field", None) \
                    == "create_nodegroup":
                count += 1
                request.session["groups_count"] = count
                break

        for idx in range(0, count, 1):
            self.fields["group_" + str(idx) + "_name"] = forms.CharField(
                label=_("Name"),
                required=True)

            self.fields["group_" + str(idx) + "_template"] = forms.ChoiceField(
                label=_("Node group template"),
                required=True,
                choices=templates)

            self.fields["group_" + str(idx) + "_count"] = forms.IntegerField(
                label=_("Count"),
                required=True,
                min_value=1
            )

    def clean(self):
        cleaned_data = super(ConfigureNodegroupsAction, self).clean()
        if cleaned_data.get("hidden_nodegroups_field", None) \
                == "create_nodegroup":
            self._errors = dict()
        return cleaned_data

    class Meta:
        name = _("Cluster Node groups")


class ConfigureNodegroups(workflows.Step):
    action_class = ConfigureNodegroupsAction
    contributes = ("hidden_nodegroups_field", )


class ConfigureClusterTemplate(workflows.Workflow):
    slug = "configure_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:cluster_templates:index"
    default_steps = (GeneralConfig, ConfigureNodegroups, )

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
        return True
