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

from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import workflows

LOG = logging.getLogger(__name__)


class GeneralConfigAction(workflows.Action):
    nodegroup_name = forms.CharField(label=_("Template Name"),
                                     required=True)

    flavor = forms.ChoiceField(label=_("OpenStack Flavor"),
                               required=True)

    hidden_configure_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_configure_field"}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        #todo get processes from plugin
        self.fields["processes"] = forms.MultipleChoiceField(
            label=_("Processes"),
            required=True,
            widget=forms.CheckboxSelectMultiple(),
            help_text=_("Processes to be launched in node group"),
            choices=[("name_node", "Name Node"),
                     ("job_tracker", "Job Tracker"),
                     ("data_node", "Data Node"),
                     ("task_tracker", "Task Tracker")])

        #todo add General Node Configuration

    def populate_flavor_choices(self, request, context):
        #todo filter images by tag, taken from context
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
        name = _("Configure Node group Template")
        help_text_template = ("nodegroup_templates/_create_general_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction


class Parameter(object):
    def __init__(self, name, param_type, required=False, choices=None):
        self.name = name
        self.required = required
        self.param_type = param_type
        self.choices = choices


def _create_step_action(name, title, parameters):
    meta = type('Meta', (object, ), dict(name=title))

    fields = {}
    contributes_field = ()
    for param in parameters:
        contributes_field += (param.name,)
        if param.param_type == "text":
            fields[param.name] = forms.CharField(label=param.name,
                                                 required=param.required)
        elif param.param_type == "bool":
            fields[param.name] = forms.BooleanField(label=param.name,
                                                    required=False)
        elif param.param_type == "dropdown":
            fields[param.name] = forms.ChoiceField(label=param.name,
                                                   required=param.required,
                                                   choices=param.choices)
    action = type(name + "Action",
                  (workflows.Action, meta),
                  fields)

    step = type(name + 'Step',
                (workflows.Step,),
                dict(name=name,
                     action_class=action,
                     contributes=contributes_field))

    return step


class ConfigureNodegroupTemplate(workflows.Workflow):
    slug = "configure_nodegroup_template"
    name = _("Create Node group Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:nodegroup_templates:index"
    default_steps = (GeneralConfig,)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        #todo manage registry celeanup
        ConfigureNodegroupTemplate._cls_registry = set([])

        #todo get tabs from api
        LOG.warning("init on configure called")
        step_form_api_name = "HDFS"
        hdfs_parameters = [Parameter("heap_size", "text", True),
                           Parameter("some_dropdown_parameter",
                                     "dropdown",
                                     True,
                                     [("val1", "Value1"),
                                      ("val2", "Value2")]),
                           Parameter("simple_checkbox_parameter", "bool")]

        test_step = _create_step_action(name=step_form_api_name,
                                        title="Configure HDFS",
                                        parameters=hdfs_parameters)

        registry = ConfigureNodegroupTemplate._cls_registry
        if (not test_step in registry):
            ConfigureNodegroupTemplate.register(test_step)

        super(ConfigureNodegroupTemplate, self).__init__(request,
                                                         context_seed,
                                                         entry_point,
                                                         *args, **kwargs)

    def handle(self, request, context):
        try:
            return True
        except Exception:
            exceptions.handle(request)
            return False


class SelectPluginAction(workflows.Action):
    plugin_name = forms.ChoiceField(label=_("Plugin name"),
                                    required=True,
                                    choices=[('Vanilla hadoop',
                                              'Vanilla hadoop')])
    hadoop_version = forms.ChoiceField(label=_("Hadoop version"),
                                       required=True,
                                       choices=[
                                           ("1.1.1", "1.1.1"),
                                           ("1.0.4", "1.0.4"),
                                           ("1.0.3", "1.0.3")])
    hidden_create_field = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"class": "hidden_create_field"}))

    def __init__(self, request, *args, **kwargs):
        super(SelectPluginAction, self).__init__(request, *args, **kwargs)

    class Meta:
        name = _("Select plugin and version")


class SelectPlugin(workflows.Step):
    action_class = SelectPluginAction
    contributes = ("plugin_name", "hadoop_version")


class CreateNodegroupTemplate(workflows.Workflow):
    slug = "create_nodegroup_template"
    name = _("Create Node group Template")
    finalize_button_name = _("Create")
    success_message = _("Created")
    failure_message = _("Could not create")
    success_url = "horizon:savanna:nodegroup_templates:index"
    default_steps = (SelectPlugin,)

    def handle(self, request, context):
        try:
            request.session["plugin_name"] = context["plugin_name"]
            request.session["hadoop_version"] = context["hadoop_version"]
            return True
        except Exception:
            exceptions.handle(request)
            return False
