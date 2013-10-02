# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2013 Red Hat Inc.
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

from django.forms.util import flatatt
from django.forms import widgets

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows

from savannadashboard.api.client import client as savannaclient

LOG = logging.getLogger(__name__)


class LabeledInput(widgets.Input):
    def render(self, name, values, attrs=None):
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        output = "<span id='%s'>%s</span>%s" %\
            ("id_%s_label" % name,
             "swift://",
             ('<input%s />' % flatatt(final_attrs)))
        return mark_safe(output)


class GeneralConfigAction(workflows.Action):
    data_source_name = forms.CharField(label=_("Name"),
                                       required=True)

    data_source_type = forms.ChoiceField(
        label=_("Data Source Type"),
        required=True,
        choices=[("swift", "Swift")],
        widget=forms.Select(attrs={"class": "data_source_type_choice"}))

    data_source_url = forms.CharField(label=_("URL"),
                                      required=True,
                                      widget=LabeledInput())

    data_source_credential_user = forms.CharField(label=_("Source username"),)

    data_source_credential_pass = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        label=_("Source password"))

    data_source_description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea)

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

    class Meta:
        name = _("Create Data Source")
        help_text_template = \
            ("data_sources/_create_data_source_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        context["source_url"] = "%s://%s" % \
            (context["general_data_source_type"],
             context["general_data_source_url"])

        return context


class CreateDataSource(workflows.Workflow):
    slug = "create_data_source"
    name = _("Create Data Source")
    finalize_button_name = _("Create")
    success_message = _("Data source created")
    failure_message = _("Could not create data source")
    success_url = "horizon:savanna:data_sources:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        savanna = savannaclient(request)
        savanna.data_sources.create(
            context["general_data_source_name"],
            context["general_data_source_description"],
            context["general_data_source_type"],
            context["source_url"],
            context["general_data_source_credential_user"],
            context["general_data_source_credential_pass"])
        return True
