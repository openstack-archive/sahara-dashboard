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
from saharaclient.api import base as api_base

from horizon import exceptions
from horizon import forms
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient


class UpdateLabelsAction(workflows.Action):
    def __init__(self, request, *args, **kwargs):
        super(UpdateLabelsAction, self).__init__(request, *args, **kwargs)
        plugin_name = [
            x['plugin_name'] for x in args if 'plugin_name' in x][0]
        plugin = saharaclient.plugin_get(request, plugin_name)
        self._serialize_labels(
            'plugin_', _("Plugin label"), plugin.plugin_labels)
        vers_labels = plugin.version_labels
        for version in vers_labels.keys():
            field_label = _("Plugin version %(version)s label") % {
                'version': version}
            self._serialize_labels(
                'version_%s_' % version, field_label, vers_labels[version])
        self.fields["plugin_name"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=plugin_name)

    def _serialize_labels(self, prefix, prefix_trans, labels):
        for name, label in labels.items():
            if not label['mutable']:
                continue
            res_name_translated = "%s: %s" % (prefix_trans, name)
            res_name = "label_%s%s" % (prefix, name)
            self.fields[res_name] = forms.BooleanField(
                label=res_name_translated,
                help_text=label['description'],
                widget=forms.CheckboxInput(),
                initial=label['status'],
                required=False,
            )

    class Meta(object):
        name = _("Plugin")
        help_text = _("Update the plugin labels")


class UpdatePluginStep(workflows.Step):
    action_class = UpdateLabelsAction
    depends_on = ('plugin_name', )

    def contribute(self, data, context):
        for name, item in data.items():
            context[name] = item
        return context


class UpdatePlugin(workflows.Workflow):
    slug = "update_plugin"
    name = _("Update Plugin")
    success_message = _("Updated")
    failure_message = _("Could not update plugin")
    success_url = "horizon:project:data_processing.data_plugins:index"
    default_steps = (UpdatePluginStep,)

    def __init__(self, request, context_seed, entry_point, *args, **kwargs):
        super(UpdatePlugin, self).__init__(
            request, context_seed, entry_point, *args, **kwargs)

    def _get_update_values(self, context):
        values = {'plugin_labels': {}, 'version_labels': {}}
        for item, item_value in context.items():
            if not item.startswith('label_'):
                continue
            name = item.split('_')[1:]
            if name[0] == 'plugin':
                values['plugin_labels'][name[1]] = {'status': item_value}
            else:
                if name[1] not in values['version_labels']:
                    values['version_labels'][name[1]] = {}
                values['version_labels'][
                    name[1]][name[2]] = {'status': item_value}
        return values

    def handle(self, request, context):
        try:
            update_values = self._get_update_values(context)
            saharaclient.plugin_update(
                request, context['plugin_name'], update_values)
            return True
        except api_base.APIException as e:
            self.error_description = str(e)
            return False
        except Exception:
            exceptions.handle(request,
                              _("Plugin update failed."))
            return False
