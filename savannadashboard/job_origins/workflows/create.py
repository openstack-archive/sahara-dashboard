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

import json
import logging

from django.utils.translation import ugettext as _

from horizon import forms
from horizon import workflows

from savannadashboard.api import client as savannaclient


LOG = logging.getLogger(__name__)


CREATE_BINARY_URL = 'horizon:savanna:job_binaries:create-job-binary'


class AdditionalLibsAction(workflows.Action):

    lib_binaries = forms.DynamicChoiceField(label=_("Choose libraries"),
                                            required=False,
                                            help_text=_("Choose the "
                                                        "binary which should"
                                                        " be used in this "
                                                        "JobOrigin."),
                                            add_item_link=CREATE_BINARY_URL,
                                            )

    lib_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput())

    def populate_lib_binaries_choices(self, request, context):
        savanna = savannaclient.Client(request)
        job_binaries = savanna.job_binaries.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', '-- not selected --'))

        return choices

    class Meta:
        name = _("Libs")


class GeneralConfigAction(workflows.Action):

    job_origin_name = forms.CharField(label=_("Name"),
                                      required=True)

    job_origin_description = forms.CharField(label=_("Description"),
                                             required=False,
                                             widget=forms.Textarea)

    main_binary = forms.DynamicChoiceField(label=_("Choose or create "
                                                   "a main binary"),
                                           required=False,
                                           help_text=_("Choose the binary "
                                                       "which should be used "
                                                       "in this JobOrigin."),
                                           add_item_link=CREATE_BINARY_URL)

    def populate_main_binary_choices(self, request, context):
        savanna = savannaclient.Client(request)
        job_binaries = savanna.job_binaries.list()

        choices = [(job_binary.id, job_binary.name)
                   for job_binary in job_binaries]
        choices.insert(0, ('', '-- not selected --'))
        return choices

    class Meta:
        name = _("Create Job Origin")
        help_text_template = "job_origins/" \
                             "_create_job_origin_help.html"


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context[k] = v
        return context


class ConfigureLibs(workflows.Step):
    action_class = AdditionalLibsAction
    template_name = "job_origins/library_template.html"

    def contribute(self, data, context):
        chosen_libs = json.loads(data.get("lib_ids", '[]'))
        for k in xrange(len(chosen_libs)):
            context["lib_" + str(k)] = chosen_libs[k]
        return context


class CreateJobOrigin(workflows.Workflow):
    slug = "create_job_origin"
    name = _("Create Job Origin")
    finalize_button_name = _("Create")
    success_message = _("Job origin created")
    failure_message = _("Could not create job origin")
    success_url = "horizon:savanna:job_origins:index"
    default_steps = (GeneralConfig, ConfigureLibs)

    def handle(self, request, context):
        savanna = savannaclient.Client(request)
        main_locations = []
        lib_locations = []

        for k in context.keys():
            if k.startswith('lib_'):
                lib_locations.append(context.get(k))

        main_locations.append(context["main_binary"])
        savanna.job_origins.create(
            context["job_origin_name"],
            main_locations,
            lib_locations,
            context["job_origin_description"])
        return True
