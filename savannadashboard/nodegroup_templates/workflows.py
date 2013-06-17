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

from horizon.api import nova
from horizon import forms
import logging

from django.contrib import messages as _messages
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import workflows

from savannadashboard.api import client as savannaclient
from savannadashboard.api import helpers
from savannadashboard.utils import workflow_helpers
from savannadashboard.utils.workflow_helpers import _create_step_action
from savannadashboard.utils.workflow_helpers import build_control


LOG = logging.getLogger(__name__)


def get_plugin_and_hadoop_version(request):
    plugin_name = request.session.get("plugin_name")
    hadoop_version = request.session.get("hadoop_version")
    return (plugin_name, hadoop_version)


class GeneralConfigAction(workflows.Action):
    nodegroup_name = forms.CharField(label=_("Template Name"),
                                     required=True)

    description = forms.CharField(label=_("Description"),
                                  required=False,
                                  widget=forms.Textarea)

    flavor = forms.ChoiceField(label=_("OpenStack Flavor"),
                               required=True)

    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        hlps = helpers.Helpers(savanna)

        plugin, hadoop_version = get_plugin_and_hadoop_version(request)
        process_choices = []
        version_details = savanna.plugins.get_version_details(plugin,
                                                              hadoop_version)

        for service, processes in version_details.node_processes.items():
            for process in processes:
                process_choices.append(
                    (str(service) + ":" + str(process), process))

        self.fields["processes"] = forms.MultipleChoiceField(
            label=_("Processes"),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            help_text=_("Processes to be launched in node group"),
            choices=process_choices)

        node_parameters = hlps.get_general_node_group_configs(plugin,
                                                              hadoop_version)
        for param in node_parameters:
            self.fields[param.name] = build_control(param)

    def populate_flavor_choices(self, request, context):
        try:
            flavors = nova.flavor_list(request)
            flavor_list = [(flavor.id, "%s" % flavor.name)
                           for flavor in flavors]
        except Exception:
            flavor_list = []
            exceptions.handle(request,
                              _('Unable to retrieve instance flavors.'))
        return sorted(flavor_list)

    def get_help_text(self):
        extra = dict()
        extra["plugin_name"] = self.request.session.get("plugin_name")
        extra["hadoop_version"] = self.request.session.get("hadoop_version")
        return super(GeneralConfigAction, self).get_help_text(extra)

    class Meta:
        name = _("Configure Node Group Template")
        help_text_template = \
            ("nodegroup_templates/_configure_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            if "hidden" in k:
                continue
            context["general_" + k] = v

        post = self.workflow.request.POST
        context['general_processes'] = post.getlist("processes")
        return context


class ConfigureNodegroupTemplate(workflows.Workflow):
    slug = "configure_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:nodegroup_templates:index"
    default_steps = (GeneralConfig,)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        #TODO(nkonovalov) manage registry cleanup
        ConfigureNodegroupTemplate._cls_registry = set([])

        savanna = savannaclient.Client(request)
        hlps = helpers.Helpers(savanna)

        plugin, hadoop_version = get_plugin_and_hadoop_version(request)

        service_parameters = hlps.get_targeted_node_group_configs(
            plugin,
            hadoop_version)
        for service, parameters in service_parameters.items():
            step = _create_step_action(service,
                                       title=service + " parameters",
                                       parameters=parameters,
                                       service=service)
            ConfigureNodegroupTemplate.register(step)

        super(ConfigureNodegroupTemplate, self).__init__(request,
                                                         context_seed,
                                                         entry_point,
                                                         *args, **kwargs)

    def is_valid(self):
        missing = self.depends_on - set(self.context.keys())
        if missing:
            raise exceptions.WorkflowValidationError(
                "Unable to complete the workflow. The values %s are "
                "required but not present." % ", ".join(missing))
        checked_steps = []

        if "general_processes" in self.context:
            checked_steps = self.context["general_processes"]
        enabled_services = set([])
        for process_name in checked_steps:
            enabled_services.add(str(process_name).split(":")[0])

        steps_valid = True
        for step in self.steps:
            process_name = str(getattr(step, "process_name", None))
            if not process_name and process_name not in enabled_services:
                continue
            if not step.action.is_valid():
                steps_valid = False
                step.has_errors = True
        if not steps_valid:
            return steps_valid
        return self.validate(self.context)

    def handle(self, request, context):
        try:
            savanna = savannaclient.Client(request)
            plugin_name = request.session.get("plugin_name")
            hadoop_version = request.session.get("hadoop_version")

            processes = []
            for service_process in context["general_processes"]:
                processes.append(str(service_process).split(":")[1])

            configs_dict = dict()
            for key, val in context.items():
                if not val:
                    continue
                if str(key).startswith("CONF"):
                    key_split = str(key).split(":")
                    service = key_split[1]
                    config = key_split[2]
                    if service not in configs_dict:
                        configs_dict[service] = dict()
                    configs_dict[service][config] = val

            LOG.info("create with config:" + str(configs_dict))

            savanna.node_group_templates.create(
                context["general_nodegroup_name"],
                plugin_name,
                hadoop_version,
                context["general_description"],
                context["general_flavor"],
                processes,
                configs_dict)
            return True
        except Exception:
            exceptions.handle(request)
            return False


class SelectPluginAction(workflows.Action,
                         workflow_helpers.PluginAndVersionMixin):
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

        savanna = savannaclient.Client(request)
        self._generate_plugin_version_fields(savanna)

    class Meta:
        name = _("Select plugin and hadoop version")
        help_text_template = ("nodegroup_templates/_create_general_help.html")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction
    contributes = ("plugin_name", "hadoop_version")

    def contribute(self, data, context):
        context = super(SelectPlugin, self).contribute(data, context)
        context["plugin_name"] = data.get('plugin_name', None)
        context["hadoop_version"] = \
            data.get(context["plugin_name"] + "_version", None)
        return context


class CreateNodegroupTemplate(workflows.Workflow):
    slug = "create_nodegroup_template"
    name = _("Create Node Group Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:nodegroup_templates:index"
    default_steps = (SelectPlugin,)

    def handle(self, request, context):
        try:
            request.session["plugin_name"] = context["plugin_name"]
            request.session["hadoop_version"] = context["hadoop_version"]
            _messages.set_level(request, _messages.WARNING)
            return True
        except Exception:
            exceptions.handle(request)
            return False
