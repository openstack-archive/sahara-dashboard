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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows

from savannadashboard.api import client as savannaclient


LOG = logging.getLogger(__name__)


class AddExtraSelectWidget(forms.Select):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select>')
        output.append("<input type='button' " +
                      "class='job_binary_add_button' value='Add' " +
                      "onclick='addExtraBinary(this);'></input>")
        return mark_safe("".join(output))


class GeneralConfigAction(workflows.Action):
    NUM_LOCATION_FIELDS = 10
    FIELDS_BEFORE_MAIN = 2
    local_binary_choices = []
    extra_binary_count = forms.CharField(widget=forms.HiddenInput())

    job_origin_name = forms.CharField(label=_("Name"),
                                      required=True)

    job_origin_description = forms.CharField(label=_("Description"),
                                             required=False,
                                             widget=forms.Textarea)

    def populate_job_origin_local_db_choices(self, request):
        savanna = savannaclient.Client(request)
        job_binaries = savanna.job_binaries.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', 'NONE'))

        return choices

    def __init__(self, request, *args, **kwargs):
        extra_fields = kwargs.pop('extra', 0)

        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        self.fields['extra_binary_count'].initial = extra_fields
        self.local_binary_choices =\
            self.populate_job_origin_local_db_choices(request)

        for i in range(self.NUM_LOCATION_FIELDS, 0, -1):
            self.fields.insert(
                self.FIELDS_BEFORE_MAIN, 'job_origin_main_%s' % i,
                forms.ChoiceField(
                    label=_("Main Binary"),
                    required=False,
                    choices=self.local_binary_choices,
                    initial=(None, "None"),
                    widget=AddExtraSelectWidget(
                        attrs={"class": "job_origin_main"})))

        for i in range(self.NUM_LOCATION_FIELDS, 0, -1):
            self.fields.insert(
                self.FIELDS_BEFORE_MAIN + self.NUM_LOCATION_FIELDS,
                'job_origin_lib_%s' % i,
                forms.ChoiceField(
                    label=_("Library"),
                    required=False,
                    choices=self.local_binary_choices,
                    initial=(None, "None"),
                    widget=AddExtraSelectWidget(
                        attrs={"class": "job_origin_lib"})))

        self.fields["extra_locations"] = forms.CharField(
            widget=forms.HiddenInput(),
            initial=self.NUM_LOCATION_FIELDS)

    class Meta:
        name = _("Create Job Origin")
        help_text_template = \
            ("job_origins/_create_job_origin_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        return context


class CreateJobOrigin(workflows.Workflow):
    slug = "create_job_origin"
    name = _("Create Job Origin")
    finalize_button_name = _("Create")
    success_message = _("Job origin created")
    failure_message = _("Could not create job origin")
    success_url = "horizon:savanna:job_origins:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        savanna = savannaclient.Client(request)
        main_locations = []
        lib_locations = []

        extra_count = 2
        for i in range(1, extra_count + 1):
            if(context["general_job_origin_main_%s" % i] != ""):
                main_locations.append(
                    context["general_job_origin_main_%s" % i])

        for i in range(1, extra_count + 1):
            if(context["general_job_origin_lib_%s" % i] != ""):
                lib_locations.append(
                    context["general_job_origin_lib_%s" % i])

        savanna.job_origins.create(
            context["general_job_origin_name"],
            main_locations,
            lib_locations,
            context["general_job_origin_description"])
        return True
