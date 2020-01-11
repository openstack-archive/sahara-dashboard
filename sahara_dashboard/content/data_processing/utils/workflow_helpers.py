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

from oslo_log import log as logging

from django.core.exceptions import ValidationError
from django.utils import safestring
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import workflows
from openstack_dashboard.api import neutron

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard import utils

LOG = logging.getLogger(__name__)


class Parameter(object):
    def __init__(self, config):
        self.name = config['name']
        self.description = config.get('description', "No description")
        self.required = not config['is_optional']
        self.default_value = config.get('default_value', None)
        self.initial_value = self.default_value
        self.param_type = config['config_type']
        self.priority = int(config.get('priority', 2))
        self.choices = config.get('config_values', None)


def build_control(parameter):
    attrs = {"priority": parameter.priority,
             "placeholder": parameter.default_value}
    if parameter.param_type == "string":
        return forms.CharField(
            widget=forms.TextInput(attrs=attrs),
            label=parameter.name,
            required=(parameter.required and
                      parameter.default_value is None),
            help_text=parameter.description,
            initial=parameter.initial_value)

    if parameter.param_type == "int":
        return forms.IntegerField(
            widget=forms.TextInput(attrs=attrs),
            label=parameter.name,
            required=parameter.required,
            help_text=parameter.description,
            initial=parameter.initial_value)

    elif parameter.param_type == "bool":
        return forms.BooleanField(
            widget=forms.CheckboxInput(attrs=attrs),
            label=parameter.name,
            required=False,
            initial=parameter.initial_value,
            help_text=parameter.description)

    elif parameter.param_type == "dropdown":
        return forms.ChoiceField(
            widget=forms.Select(attrs=attrs),
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
                       dict(help_text_template=("nodegroup_templates/"
                                                "_fields_help.html")))

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


def build_node_group_fields(action, name, template, count, serialized=None):
    action.fields[name] = forms.CharField(
        label=_("Name"),
        widget=forms.TextInput())

    action.fields[template] = forms.CharField(
        label=_("Node group cluster"),
        widget=forms.HiddenInput())

    action.fields[count] = forms.IntegerField(
        label=_("Count"),
        min_value=0,
        widget=forms.HiddenInput())
    action.fields[serialized] = forms.CharField(
        widget=forms.HiddenInput())


def build_interface_argument_fields(
        action, name, description, mapping_type, location, value_type,
        required, default_value):
    action.fields[name] = forms.CharField(
        label=_("Name"),
        widget=forms.TextInput(),
        required=True)
    action.fields[description] = forms.CharField(
        label=_("Description"),
        widget=forms.TextInput(),
        required=False)
    action.fields[mapping_type] = forms.ChoiceField(
        label=_("Mapping Type"),
        widget=forms.Select(),
        required=True,
        choices=[("args", _("Positional Argument")),
                 ("configs", _("Configuration Value")),
                 ("params", _("Named Parameter"))])
    action.fields[location] = forms.CharField(
        label=_("Location"),
        widget=forms.TextInput(),
        required=True)
    action.fields[value_type] = forms.ChoiceField(
        label=_("Value Type"),
        widget=forms.Select(),
        required=True,
        choices=[("string", _("String")),
                 ("number", _("Number")),
                 ("data_source", _("Data Source"))])
    action.fields[required] = forms.BooleanField(
        widget=forms.CheckboxInput(),
        label=_("Required"),
        required=False,
        initial=True)
    action.fields[default_value] = forms.CharField(
        label=_("Default Value"),
        widget=forms.TextInput(),
        required=False)


def parse_configs_from_context(context, defaults):
    configs_dict = dict()
    for key, val in context.items():
        if str(key).startswith("CONF"):
            key_split = str(key).split(":")
            service = key_split[1]
            config = key_split[2]
            if service not in configs_dict:
                configs_dict[service] = dict()
            if val is None:
                continue
            if str(defaults[service][config]) == str(val):
                continue
            configs_dict[service][config] = val
    return configs_dict


def get_security_groups(request, security_group_ids):
    security_groups = []
    for group in security_group_ids or []:
        try:
            security_groups.append(neutron.security_group_get(
                request, group))
        except Exception:
            LOG.info(_('Unable to retrieve security group %(group)s.') %
                     {'group': group})
            security_groups.append({'name': group})

    return security_groups


def get_plugin_and_hadoop_version(request):
    plugin_name = None
    hadoop_version = None
    # In some cases request contains valuable info in both GET and POST methods
    req = request.GET.copy()
    req.update(request.POST)
    if req.get("plugin_name"):
        plugin_name = req["plugin_name"]
        hadoop_version = (
            req.get("plugin_version", None) or req["hadoop_version"]
        )
    return plugin_name, hadoop_version


def clean_node_group(node_group):
    node_group_copy = dict((key, value)
                           for key, value in node_group.items() if value)

    for key in ["id", "created_at", "updated_at"]:
        if key in node_group_copy:
            node_group_copy.pop(key)

    return node_group_copy


def populate_image_choices(self, request, context, empty_choice=False):
    try:
        all_images = saharaclient.image_list(request)

        plugin, hadoop_version = get_plugin_and_hadoop_version(request)

        details = saharaclient.plugin_get_version_details(request,
                                                          plugin,
                                                          hadoop_version)
        choices = [(image.id, image.name) for image in all_images
                   if (set(details.required_image_tags).
                       issubset(set(image.tags)))]
    except Exception:
        exceptions.handle(request,
                          _("Unable to fetch image choices."))
        choices = []
    if empty_choice:
        choices = [(None, _('No image specified'))] + choices
    if not choices:
        choices.append(("", _("No Images Available")))

    return choices


class PluginAndVersionMixin(object):
    def _generate_plugin_version_fields(self, sahara):
        plugins = [p for p in sahara.plugins.list()
                   if is_plugin_not_hidden_for_user(p)]
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin Name"),
            choices=plugin_choices,
            widget=forms.Select(
                attrs={"class": "plugin_name_choice switchable",
                       'data-slug': 'pluginname'}))

        for plugin in plugins:
            versions = [(version, version)
                        for version in get_enabled_versions(plugin)]
            version_choices = sorted(
                versions,
                reverse=True,
                key=lambda v: utils.smart_sort_helper(v[0]))
            field_name = plugin.name + "_version"
            choice_field = forms.ChoiceField(
                label=_("Version"),
                choices=version_choices,
                widget=forms.Select(
                    attrs={"class": "plugin_version_choice switched "
                           + field_name + "_choice",
                           "data-switch-on": "pluginname",
                           "data-pluginname-%s" % plugin.name: _("Version")})
            )
            self.fields[field_name] = choice_field


class PatchedDynamicWorkflow(workflows.Workflow):
    """Overrides Workflow to fix its issues."""

    def _ensure_dynamic_exist(self):
        if not hasattr(self, 'dynamic_steps'):
            self.dynamic_steps = list()

    def _register_step(self, step):
        # Use that method instead of 'register' to register step.
        # Note that a step could be registered in descendant class constructor
        # only before this class constructor is invoked.
        self._ensure_dynamic_exist()
        self.dynamic_steps.append(step)

    def _order_steps(self):
        # overrides method of Workflow
        # crutch to fix https://bugs.launchpad.net/horizon/+bug/1196717
        # and another not filed issue that dynamic creation of tabs is
        # not thread safe
        self._ensure_dynamic_exist()

        self._registry = dict([(step, step(self))
                               for step in self.dynamic_steps])

        return list(self.default_steps) + self.dynamic_steps


class ServiceParametersWorkflow(PatchedDynamicWorkflow):
    """Base class for Workflows having services tabs with parameters."""

    def _populate_tabs(self, general_parameters, service_parameters):
        # Populates tabs for 'general' and service parameters
        # Also populates defaults and initial values
        self.defaults = dict()

        self._init_step('general', 'General Parameters', general_parameters)

        for service, parameters in service_parameters.items():
            self._init_step(service, service + ' Parameters', parameters)

    def _init_step(self, service, title, parameters):
        if not parameters:
            return

        self._populate_initial_values(service, parameters)

        step = _create_step_action(service, title=title, parameters=parameters,
                                   service=service)

        self.defaults[service] = dict()
        for param in parameters:
            self.defaults[service][param.name] = param.default_value

        self._register_step(step)

    def _set_configs_to_copy(self, configs):
        self.configs_to_copy = configs

    def _populate_initial_values(self, service, parameters):
        if not hasattr(self, 'configs_to_copy'):
            return

        configs = self.configs_to_copy

        for param in parameters:
            if (service in configs and
                    param.name in configs[service]):
                param.initial_value = configs[service][param.name]


class StatusFormatMixin(workflows.Workflow):
    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        super(StatusFormatMixin, self).__init__(request,
                                                context_seed,
                                                entry_point,
                                                *args,
                                                **kwargs)

    def format_status_message(self, message):
        error_description = getattr(self, 'error_description', None)

        if error_description:
            return error_description
        else:
            return message % self.context[self.name_property]


class ShareWidget(forms.MultiWidget):
    def __init__(self, choices=()):
        widgets = []
        for choice in choices:
            widgets.append(forms.CheckboxInput(
                attrs={
                    "label": choice[1],
                    "value": choice[0],
                }))
            widgets.append(forms.TextInput())
            widgets.append(forms.Select(
                choices=(("rw", _("Read/Write")), ("ro", _("Read only")))))
        super(ShareWidget, self).__init__(widgets)

    def decompress(self, value):
        if value:
            values = []
            for share in value:
                values.append(value[share]["id"])
                values.append(value[share]["path"])
                values.append(value[share]["access_level"])
            return values
        return [None] * len(self.widgets)

    def format_output(self, rendered_widgets):
        output = []
        output.append("<table>")
        output.append("<tr><th>Share</th><th>Enabled</th>"
                      "<th>Path</th><th>Permissions</th></tr>")
        for i, widget in enumerate(rendered_widgets):
            item_widget_index = i % 3
            if item_widget_index == 0:
                output.append("<tr>")
                output.append(
                    "<td class='col-sm-2 small-padding'>%s</td>" %
                    self.widgets[i].attrs["label"])
            # The last 2 form field td need get a larger size
            if item_widget_index in [1, 2]:
                size = 4
            else:
                size = 2
            output.append("<td class='col-sm-%s small-padding'>" % size
                          + widget + "</td>")
            if item_widget_index == 2:
                output.append("</tr>")
        output.append("</table>")
        return safestring.mark_safe('\n'.join(output))


class MultipleShareChoiceField(forms.MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')
        if not isinstance(value, list):
            raise ValidationError(
                _("The value of shares must be a list of values")
            )


def is_plugin_not_hidden_for_user(plugin):
    hidden_lbl = plugin.plugin_labels.get('hidden')
    if hidden_lbl and hidden_lbl['status']:
        return False
    if get_enabled_versions(plugin):
        return True
    return False


def get_enabled_versions(plugin):
    lbs = plugin.version_labels

    versions = []
    for version, data in lbs.items():
        if data.get('enabled', {'status': True}).get('status', True):
            versions.append(version)

    if not plugin.plugin_labels.get(
            'enabled', {'status': True}).get('status', True):
        versions = []
    return versions


def is_version_of_plugin_deprecated(plugin, version):
    lbs = plugin.version_labels
    for iter_version, data in lbs.items():
        if iter_version == version:
            if data.get('deprecated', {'status': False}).get('status', False):
                return True
            else:
                return False
