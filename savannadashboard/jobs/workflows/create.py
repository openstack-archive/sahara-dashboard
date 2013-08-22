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

from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows

from savannadashboard.api import client as savannaclient

LOG = logging.getLogger(__name__)


class GeneralConfigAction(workflows.Action):
    job_name = forms.CharField(label=_("Job Name"),
                               required=True)

    job_type = forms.ChoiceField(
        label=_("Job Type"),
        required=True,
        choices=[("Pig", "Pig"), ("Hive", "Hive"),
                 ("Oozie", "Oozie"), ("Jar", "Jar"),
                 ("StreamingAPI", "Streaming API")],
        widget=forms.Select(attrs={"class": "job_type_choice"}))

    job_input_type = forms.ChoiceField(
        label=_("Input Type"),
        required=True,
        choices=[("swift", "Swift")],
        widget=forms.Select(attrs={"class": "job_input_type_choice"}))

    job_output_type = forms.ChoiceField(
        label=_("Output Type"),
        required=True,
        choices=[("swift", "Swift")],
        widget=forms.Select(attrs={"class": "job_output_type_choice"}))

    job_origin = forms.ChoiceField(
        label=_("Job Origin"),
        required=True,
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "job_origin_choice"}))

    job_description = forms.CharField(label=_("Job Description"),
                                      required=False,
                                      widget=forms.Textarea)

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

    def populate_job_origin_choices(self, request, context):
        savanna = savannaclient.Client(request)
        job_origins = savanna.job_origins.list()

        choices = [(job_origin.id, job_origin.name)
                   for job_origin in job_origins]

        return choices

    class Meta:
        name = _("Create Job")
        help_text_template = \
            ("jobs/_create_job_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        return context


class CreateJob(workflows.Workflow):
    slug = "create_job"
    name = _("Create Job")
    finalize_button_name = _("Create")
    success_message = _("Job created")
    failure_message = _("Could not create job")
    success_url = "horizon:savanna:jobs:index"
    default_steps = (GeneralConfig, )

    def handle(self, request, context):
        savanna = savannaclient.Client(request)
        savanna.jobs.create(
            context["general_job_name"],
            context["general_job_description"],
            context["general_job_type"],
            context["general_job_input_type"],
            context["general_job_output_type"],
            context["general_job_origin"])
        return True
