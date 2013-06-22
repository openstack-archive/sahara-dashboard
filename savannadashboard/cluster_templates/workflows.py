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

from django.contrib import messages as _messages
from django.utils.translation import ugettext as _
import json

from horizon import exceptions
from horizon import forms
from horizon import workflows

import savannadashboard.api.api_objects as api_objects
from savannadashboard.api import client as savannaclient
from savannadashboard.api import helpers as helpers
import savannadashboard.utils.workflow_helpers as whelpers

LOG = logging.getLogger(__name__)


class SelectPluginAction(workflows.Action):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        plugins = savanna.plugins.list()
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
            request.session.pop("ignore_idxs", None)
            request.session.pop("groups_count", None)
            _messages.set_level(request, _messages.WARNING)
            return True
        except Exception:
            exceptions.handle(request)
            return False


class GeneralConfigAction(workflows.Action):
    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    hidden_to_delete_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_to_delete_field"}))

    cluster_template_name = forms.CharField(label=_("Template Name"),
                                            required=True)

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea)

    #base_image = forms.ChoiceField(label=_("Base Image"),
    #                               required=True)

    #separate_machines = forms.BooleanField(
    #    label=_("Run data nodes on separate machines"),
    #    required=False)
    #def populate_base_image_choices(self, request, context):
    #    public_images, _more = glance.image_list_detailed(request)
    #    return [(image.id, image.name) for image in public_images]

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


class ConfigureGeneralParametersAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(ConfigureGeneralParametersAction, self). \
            __init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        plugin_name = request.session["plugin_name"]
        hadoop_version = request.session["hadoop_version"]

        parameters = helpers.Helpers(savanna).get_cluster_general_configs(
            plugin_name,
            hadoop_version)

        for param in parameters:
            self.fields[param.name] = whelpers.build_control(param)

    class Meta:
        name = _("General Cluster Configurations")


class ConfigureGeneralParameters(workflows.Step):
    action_class = ConfigureGeneralParametersAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["cluster_" + k] = v
        return context


class ConfigureNodegroupsAction(workflows.Action):
    hidden_nodegroups_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_nodegroups_field"}))
    forms_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(ConfigureNodegroupsAction, self). \
            __init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        self.templates = savanna.node_group_templates.find(
            plugin_name=request.session.get("plugin_name"),
            hadoop_version=request.session.get("hadoop_version"))

        self.groups = []
        if 'forms_ids' in request._post:
            for id in json.loads(request._post['forms_ids']):
                group_name = "group_name_" + str(id)
                template_id = "template_id_" + str(id)
                count = "count_" + str(id)
                self.groups.append({"name": request._post[group_name],
                                    "template_id": request._post[template_id],
                                    "count": request._post[count],
                                    "id": id})

                self.fields[group_name] = forms.CharField(
                    label=_("Name"),
                    required=True,
                    widget=forms.TextInput())

                self.fields[template_id] = forms.CharField(
                    label=_("Node group template"),
                    required=True,
                    widget=forms.HiddenInput())

                self.fields[count] = forms.IntegerField(
                    label=_("Count"),
                    required=True,
                    min_value=1,
                    widget=forms.HiddenInput())

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
    template_name = "cluster_templates/cluster_node_groups_template.html"

    def contribute(self, data, context):
        for k, v in data.items():
            context["ng_" + k] = v
        return context


class ConfigureClusterTemplate(workflows.Workflow):
    slug = "configure_cluster_template"
    name = _("Create Cluster Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:cluster_templates:index"
    default_steps = (GeneralConfig,
                     ConfigureNodegroups,
                     ConfigureGeneralParameters, )

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        ConfigureClusterTemplate._cls_registry = set([])

        savanna = savannaclient.Client(request)
        hlps = helpers.Helpers(savanna)

        plugin_name = request.session.get("plugin_name")
        hadoop_version = request.session.get("hadoop_version")

        service_parameters = hlps.get_targeted_cluster_configs(
            plugin_name,
            hadoop_version)

        self.defaults = dict()
        for service, parameters in service_parameters.items():
            if not parameters:
                continue
            step = whelpers._create_step_action(service,
                                                title=service + " parameters",
                                                parameters=parameters,
                                                service=service)
            ConfigureClusterTemplate.register(step)
            for param in parameters:
                if service not in self.defaults:
                    self.defaults[service] = dict()
                self.defaults[service][param.name] = param.default_value

        super(ConfigureClusterTemplate, self).__init__(request,
                                                       context_seed,
                                                       entry_point,
                                                       *args, **kwargs)

    def is_valid(self):
        steps_valid = True
        for step in self.steps:
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
                errors_fields = []
                for k, v in step.action.errors.items():
                    errors_fields.append(k)
                step.action.errors_fields = errors_fields
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            savanna = savannaclient.Client(request)
            node_groups = []
            configs_dict = whelpers.parse_configs_from_context(context,
                                                               self.defaults)
            configs_dict["general"] = dict()

            ids = json.loads(context['ng_forms_ids'])
            for id in ids:
                name = context['ng_group_name_' + str(id)]
                template_id = context['ng_template_id_' + str(id)]
                count = context['ng_count_' + str(id)]
                ng = api_objects.NodeGroup(name,
                                           template_id,
                                           count=count)
                node_groups.append(ng)

            #TODO(nkonovalov): Fix client to support default_image_id
            savanna.cluster_templates.create(
                context["general_cluster_template_name"],
                request.session.get("plugin_name"),
                request.session.get("hadoop_version"),
                context["general_description"],
                configs_dict,
                node_groups)
            return True
        except Exception as ex:
            print ex
            return False
