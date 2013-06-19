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

from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows


class Parameter(object):
    def __init__(self, config):
        self.name = config['name']
        self.description = config.get('description', "No description")
        self.required = not config['is_optional']
        self.default_value = config.get('default_value', None)
        self.param_type = config['config_type']
        self.priority = int(config.get('priority', 2))


def build_control(parameter):
    attrs = {"priority": parameter.priority,
             "placeholder": parameter.default_value}
    if parameter.param_type == "string":
        return forms.CharField(
            widget=forms.TextInput(attrs=attrs),
            label=parameter.name,
            required=(parameter.required and
                      parameter.default_value is None),
            help_text=parameter.description)

    if parameter.param_type == "int":
        return forms.IntegerField(
            widget=forms.TextInput(attrs=attrs),
            label=parameter.name,
            required=(parameter.required and
                      parameter.default_value is None),
            help_text=parameter.description)

    elif parameter.param_type == "bool":
        return forms.BooleanField(
            widget=forms.CheckboxInput(attrs=attrs),
            label=parameter.name,
            required=False,
            initial=parameter.default_value,
            help_text=parameter.description)

    elif parameter.param_type == "dropdown":
        return forms.ChoiceField(
            widget=forms.CheckboxInput(attrs=attrs),
            label=parameter.name,
            required=parameter.required,
            choices=parameter.choices,
            help_text=parameter.description)


def _create_step_action(name, title, parameters, advanced_fields=None,
                        service=None):
    class_fields = {}
    contributes_field = ()
    for param in parameters:
        field_name = "CONF:" + service + ":" + param.name
        contributes_field += (field_name,)
        class_fields[field_name] = build_control(param)

    if advanced_fields is not None:
        for ad_field_name, ad_field_value in advanced_fields:
            class_fields[ad_field_name] = ad_field_value

    action_meta = type('Meta', (object, ),
                       dict(help_text_template="nodegroup_templates/"
                                               "_fields_help.html"))

    class_fields['Meta'] = action_meta
    action = type(str(title),
                  (workflows.Action,),
                  class_fields)

    step_meta = type('Meta', (object,), dict(name=title))
    step = type(str(name),
                (workflows.Step, ),
                dict(name=name,
                     process_name=name,
                     action_class=action,
                     contributes=contributes_field,
                     Meta=step_meta))

    return step


class PluginAndVersionMixin(object):
    def _generate_plugin_version_fields(self, savanna):
        plugins = savanna.plugins.list()
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin Name"),
            required=True,
            choices=plugin_choices,
            widget=forms.Select(attrs={"class": "plugin_name_choice"}))

        for plugin in plugins:
            field_name = plugin.name + "_version"
            choice_field = forms.ChoiceField(
                label=_("Hadoop Version"),
                required=True,
                choices=[(version, version) for version in plugin.versions],
                widget=forms.Select(
                    attrs={"class": "plugin_version_choice "
                                    + field_name + "_choice"})
            )
            self.fields[field_name] = choice_field
