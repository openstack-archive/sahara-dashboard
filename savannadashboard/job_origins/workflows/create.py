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
    job_origin_name = forms.CharField(label=_("Name"),
                                      required=True)

    job_origin_credential_user = forms.CharField(label=_("Origin username"),
                                                 required=True)

    job_origin_credential_pass = forms.CharField(
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        label=_("Origin password"),
        required=True)

    job_storage_type = forms.ChoiceField(
        label=_("Job Storage Type"),
        required=True,
        choices=[("internal", "Savanna DB"),
                 ("swift", "Swift"),
                 ("hdfs", "HDFS")],
        widget=forms.Select(
            attrs={"class": "job_storage_type_choice"}))

    job_origin_location = forms.CharField(label=_("Job Storage Location"),
                                          required=True)

    job_origin_description = forms.CharField(label=_("Description"),
                                             required=False,
                                             widget=forms.Textarea)

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

    class Meta:
        name = _("Create Job Origin")
        help_text_template = \
            ("job_origins/_create_job_origin_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("hidden_configure_field", )

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
        savanna.job_origins.create(
            context["general_job_origin_name"],
            context["general_job_storage_type"],
            context["general_job_origin_credential_user"],
            context["general_job_origin_credential_pass"],
            context["general_job_origin_location"],
            context["general_job_origin_description"])
        return True
