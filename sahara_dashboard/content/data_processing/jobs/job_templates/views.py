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

from django import http
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from sahara_dashboard.api import sahara as saharaclient
import sahara_dashboard.content.data_processing.jobs.job_templates.tables \
    as jt_tables
import sahara_dashboard.content.data_processing.jobs.job_templates.tabs \
    as _tabs
import sahara_dashboard.content.data_processing.jobs.job_templates \
    .workflows.create as create_flow
import sahara_dashboard.content.data_processing.jobs.job_templates \
    .workflows.launch as launch_flow
from sahara_dashboard.content.data_processing.utils import helpers


class CreateJobView(workflows.WorkflowView):
    workflow_class = create_flow.CreateJob
    success_url = "horizon:project:data_processing.jobs:create-job"
    classes = ("ajax-modal",)
    template_name = "job_templates/create.html"
    page_title = _("Create Job Template")


class JobTemplateDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ job.name|default:job.id }}"

    @memoized.memoized_method
    def get_object(self):
        j_id = self.kwargs["job_id"]
        try:
            return saharaclient.job_get(self.request, j_id)
        except Exception:
            msg = _('Unable to retrieve details for job template "%s".') % j_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(JobTemplateDetailsView, self).\
            get_context_data(**kwargs)
        job_template = self.get_object()
        context['job'] = job_template
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(job_template)
        return context

    def _get_actions(self, job_template):
        table = jt_tables.JobTemplatesTable(self.request)
        return table.render_row_actions(job_template)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing.jobs:jobs")


class LaunchJobView(workflows.WorkflowView):
    workflow_class = launch_flow.LaunchJob
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    ajax_template_name = "job_templates/launch_ajax.html"
    template_name = "job_templates/launch.html"
    page_title = _("Launch Job")

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            if request.GET.get("json", None):
                job_id = request.GET.get("job_id")
                job_type = saharaclient.job_get(request, job_id).type
                return http.HttpResponse(json.dumps({"job_type": job_type}),
                                         content_type='application/json')
        return super(LaunchJobView, self).get(request, args, kwargs)

    def get_context_data(self, **kwargs):
        context = super(LaunchJobView, self).get_context_data(**kwargs)
        context["cl_name_state_map"] = self.get_cluster_choices(self.request)
        context["status_message_map"] = json.dumps(helpers.STATUS_MESSAGE_MAP)
        return context

    def get_cluster_choices(self, request):
        choices = []
        try:
            clusters = saharaclient.cluster_list(request)
            choices = [
                ("%s %s" % (cl.name, helpers.ALLOWED_STATUSES.get(cl.status)),
                 cl.status)
                for cl in clusters if (cl.status in helpers.ALLOWED_STATUSES)]
        except Exception:
            exceptions.handle(request, _("Unable to fetch clusters."))
        return choices


class LaunchJobNewClusterView(workflows.WorkflowView):
    workflow_class = launch_flow.LaunchJobNewCluster
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    template_name = "job_templates/launch.html"
    page_title = _("Launch Job")

    def get_context_data(self, **kwargs):
        context = super(LaunchJobNewClusterView, self).\
            get_context_data(**kwargs)
        return context


class ChoosePluginView(workflows.WorkflowView):
    workflow_class = launch_flow.ChosePluginVersion
    success_url = "horizon:project:data_processing.jobs"
    classes = ("ajax-modal",)
    template_name = "job_templates/launch.html"
    page_title = _("Launch Job")

    def get_context_data(self, **kwargs):
        context = super(ChoosePluginView, self).get_context_data(**kwargs)
        return context
