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

import json
import logging

from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows

from savannadashboard.api.client import client as savannaclient


LOG = logging.getLogger(__name__)


class AdditionalLibsAction(workflows.Action):

    lib_binaries = forms.ChoiceField(label=_("Choose libraries"),
                                     required=False)

    lib_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def populate_lib_binaries_choices(self, request, context):
        savanna = savannaclient(request)
        job_binaries = savanna.job_binaries.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', '-- not selected --'))

        return choices

    class Meta:
        name = _("Libs")
        help_text_template = "jobs/_create_job_libs_help.html"


class GeneralConfigAction(workflows.Action):

    job_name = forms.CharField(label=_("Name"),
                               required=True)

    job_type = forms.ChoiceField(label=_("Job Type"),
                                 required=True)

    main_binary = forms.ChoiceField(label=_("Choose a main binary"),
                                    required=False,
                                    help_text=_("Choose the binary which "
                                                "should be used in this "
                                                "Job."))

    job_description = forms.CharField(label=_("Description"),
                                      required=False,
                                      widget=forms.Textarea)

    def populate_job_type_choices(self, request, context):
        choices = [("Pig", "Pig"), ("Hive", "Hive"),
                   ("Jar", "Jar")]
        return choices

    def populate_main_binary_choices(self, request, context):
        savanna = savannaclient(request)
        job_binaries = savanna.job_binaries.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', '-- not selected --'))
        return choices

    class Meta:
        name = _("Create Job")
        help_text_template = "jobs/_create_job_help.html"


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction
    contributes = ("job_name", "job_type", "job_description", "main_binary")


class ConfigureLibs(workflows.Step):
    action_class = AdditionalLibsAction
    template_name = "jobs/library_template.html"

    def contribute(self, data, context):
        chosen_libs = json.loads(data.get("lib_ids", '[]'))
        for k in xrange(len(chosen_libs)):
            context["lib_" + str(k)] = chosen_libs[k]
        return context


class CreateJob(workflows.Workflow):
    slug = "create_job"
    name = _("Create Job")
    finalize_button_name = _("Create")
    success_message = _("Job created")
    failure_message = _("Could not create job")
    success_url = "horizon:savanna:jobs:index"
    default_steps = (GeneralConfig, ConfigureLibs)

    def handle(self, request, context):
        savanna = savannaclient(request)
        main_locations = []
        lib_locations = []

        for k in context.keys():
            if k.startswith('lib_'):
                lib_locations.append(context.get(k))

        if context.get("main_binary", None):
            main_locations.append(context["main_binary"])

        savanna.jobs.create(
            context["job_name"],
            context["job_type"],
            main_locations,
            lib_locations,
            context["job_description"])
        return True
