# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import template
from django.template import defaultfilters
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import helpers
from sahara_dashboard import utils


class ChoosePluginForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(ChoosePluginForm, self).__init__(request, *args, **kwargs)
        self._generate_plugin_version_fields(request)
        self.help_text_template = ("cluster_wizard/"
                                   "_plugin_select_help.html")

    def handle(self, request, context):
        try:
            hlps = helpers.Helpers(request)
            hlps.reset_guide()
            plugin_name = context["plugin_name"]
            request.session["plugin_name"] = plugin_name
            request.session["plugin_version"] = (
                context[plugin_name + "_version"])
            messages.success(request, _("Cluster type chosen"))
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to set cluster type"))
            return False

    def _generate_plugin_version_fields(self, request):
        sahara = saharaclient.client(request)
        plugins = sahara.plugins.list()
        plugin_choices = [(plugin.name, plugin.title) for plugin in plugins]

        self.fields["plugin_name"] = forms.ChoiceField(
            label=_("Plugin Name"),
            choices=plugin_choices,
            widget=forms.Select(attrs={"class": "switchable",
                                       "data-slug": "plugin"}))

        for plugin in plugins:
            field_name = plugin.name + "_version"
            version_choices = (sorted(
                [(version, version) for version in plugin.versions],
                reverse=True, key=lambda v: utils.smart_sort_helper(v[0]))
            )
            choice_field = forms.ChoiceField(
                label=_("Version"),
                required=False,
                choices=version_choices,
                widget=forms.Select(
                    attrs={"class": "switched",
                           "data-switch-on": "plugin",
                           "data-plugin-" + plugin.name: plugin.title})
            )
            self.fields[field_name] = choice_field

    def get_help_text(self, extra_context=None):
        text = ""
        extra_context = extra_context or {}
        if self.help_text_template:
            tmpl = template.loader.get_template(self.help_text_template)
            text += tmpl.render(extra_context, self.request)
        else:
            text += defaultfilters.linebreaks(force_text(self.help_text))
        return defaultfilters.safe(text)

    class Meta(object):
        name = _("Choose plugin type and version")


class ChooseTemplateForm(forms.SelfHandlingForm):
    guide_ngt = forms.ChoiceField(
        label=_("Node Group Template"),
        widget=forms.Select())

    def __init__(self, request, *args, **kwargs):
        super(ChooseTemplateForm, self).__init__(request, *args, **kwargs)
        self.help_text_template = ("cluster_wizard/"
                                   "_ngt_select_help.html")

        self.fields["guide_ngt"].choices = \
            self.populate_guide_ngt_choices()

        template_type = getattr(
            self.request, self.request.method).get("guide_template_type")
        if template_type:
            self.fields["guide_template_type"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(),
                initial=template_type)

        plugin_name = getattr(
            self.request, self.request.method).get("plugin_name")
        if plugin_name:
            self.fields["plugin_name"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(),
                initial=plugin_name)

        plugin_version = getattr(
            self.request, self.request.method).get("hadoop_version")
        if plugin_version:
            self.fields["hadoop_version"] = forms.CharField(
                required=False,
                widget=forms.HiddenInput(),
                initial=plugin_version)

    def populate_guide_ngt_choices(self):
        plugin = getattr(self.request, self.request.method).get("plugin_name")
        version = getattr(
            self.request, self.request.method).get("hadoop_version")
        data = saharaclient.nodegroup_template_find(self.request,
                                                    plugin_name=plugin,
                                                    hadoop_version=version)
        choices = [("%s|%s" % (ngt.name, ngt.id), ngt.name)
                   for ngt in data]
        return choices

    def handle(self, request, context):
        try:
            name_key = context["guide_template_type"] + "_name"
            id_key = context["guide_template_type"] + "_id"
            (name, id) = context["guide_ngt"].split("|")
            request.session[name_key] = name
            request.session[id_key] = id
            messages.success(request, _("Job type chosen"))
            return True
        except Exception:
            exceptions.handle(request,
                              _("Unable to set node group template"))
            return False
