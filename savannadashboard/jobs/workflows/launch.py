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

from savannadashboard.api.client import client as savannaclient

LOG = logging.getLogger(__name__)


class GeneralConfigAction(workflows.Action):
    cluster = forms.ChoiceField(
        label=_("Cluster"),
        required=True,
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "cluster_choice"}))

    job_input = forms.ChoiceField(
        label=_("Input"),
        required=True,
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "job_input_choice"}))

    job_output = forms.ChoiceField(
        label=_("Output"),
        required=True,
        initial=(None, "None"),
        widget=forms.Select(attrs={"class": "job_output_choice"}))

    def __init__(self, request, *args, **kwargs):
        super(GeneralConfigAction, self).__init__(request, *args, **kwargs)

        if request.REQUEST.get("job_id", None) is None:
            self.fields["job"] = forms.ChoiceField(
                label=_("Job"),
                required=True)
            self.fields["job"].choices = self.populate_job_choices(request)
        else:
            self.fields["job"] = forms.CharField(
                widget=forms.HiddenInput(),
                initial=request.REQUEST.get("job_id", None))

    def populate_cluster_choices(self, request, context):
        savanna = savannaclient(request)
        clusters = savanna.clusters.list()

        choices = [(cluster.id, cluster.name)
                   for cluster in clusters]

        return choices

    def populate_job_input_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def populate_job_output_choices(self, request, context):
        return self.get_data_source_choices(request, context)

    def get_data_source_choices(self, request, context):
        savanna = savannaclient(request)
        data_sources = savanna.data_sources.list()

        choices = [(data_source.id, data_source.name)
                   for data_source in data_sources]

        return choices

    def populate_job_choices(self, request):
        savanna = savannaclient(request)
        jobs = savanna.jobs.list()

        choices = [(job.id, job.name)
                   for job in jobs]

        return choices

    class Meta:
        name = _("Job")
        help_text_template = \
            ("jobs/_launch_job_help.html")


class JobConfigAction(workflows.Action):
    config = forms.CharField(
        label=_("Job Config"),
        required=False,
        widget=forms.Textarea())

    def __init__(self, request, *args, **kwargs):
        super(JobConfigAction, self).__init__(request, *args, **kwargs)
        # TODO(croberts) pre-populate config with job-type
        # appropriate config settings

    class Meta:
        name = _("Configure")
        help_text_template = \
            ("jobs/_launch_job_configure_help.html")


class GeneralConfig(workflows.Step):
    action_class = GeneralConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["general_" + k] = v

        return context


class JobConfig(workflows.Step):
    action_class = JobConfigAction

    def contribute(self, data, context):
        for k, v in data.items():
            context["job_" + k] = v

        return context


class LaunchJob(workflows.Workflow):
    slug = "launch_job"
    name = _("Launch Job")
    finalize_button_name = _("Launch")
    success_message = _("Job launched")
    failure_message = _("Could not launch job")
    success_url = "horizon:savanna:jobs:index"
    default_steps = (GeneralConfig, JobConfig)

    def handle(self, request, context):
        savanna = savannaclient(request)
        job_config = context.get("job_config")
        if not job_config:
            job_config = {}
        savanna.job_executions.create(
            context["general_job"],
            context["general_cluster"],
            context["general_job_input"],
            context["general_job_output"],
            job_config)

        print job_config
        return True
