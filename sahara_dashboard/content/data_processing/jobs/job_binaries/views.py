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

from django import http
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
import django.views

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon.utils import memoized

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.utils \
    import helpers
from sahara_dashboard.content.data_processing.jobs. \
    job_binaries import forms as job_binary_forms
from sahara_dashboard.content.data_processing.jobs. \
    job_binaries import tabs as _tabs
from sahara_dashboard.content.data_processing.jobs.job_binaries \
    import tables as jb_tables


class CreateJobBinaryView(forms.ModalFormView):
    form_class = job_binary_forms.JobBinaryCreateForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.jobs:index')
    classes = ("ajax-modal",)
    template_name = "job_binaries/create.html"
    page_title = _("Create Job Binary")
    submit_url = ('horizon:project:data_processing.'
                  'jobs:create-job-binary')
    submit_label = _("Create")

    def get_success_url(self):
        hlps = helpers.Helpers(self.request)
        if hlps.is_from_guide():
            self.success_url = reverse_lazy(
                "horizon:project:data_processing.wizard:jobex_guide")
        return self.success_url

    def get_context_data(self, **kwargs):
        context = super(CreateJobBinaryView, self).get_context_data(**kwargs)
        context['submit_url'] = reverse(self.submit_url, kwargs=self.kwargs)
        return context


class EditJobBinaryView(CreateJobBinaryView):
    form_class = job_binary_forms.JobBinaryEditForm
    page_title = _("Edit Job Binary")
    submit_url = ('horizon:project:data_processing.'
                  'jobs:edit-job-binary')
    submit_label = _("Update")

    @memoized.memoized_method
    def get_object(self):
        jb_id = self.kwargs["job_binary_id"]
        try:
            return saharaclient.job_binary_get(self.request, jb_id)
        except Exception:
            msg = _('Unable to retrieve job binary "%s".') % jb_id
            redirect = reverse(
                "horizon:project:data_processing.jobs:job-binaries")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(EditJobBinaryView, self).get_initial()
        initial['job_binary_id'] = self.kwargs['job_binary_id']
        initial['job_binary'] = self.get_object()
        return initial


class JobBinaryDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobBinaryDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ job_binary.name|default:job_binary.id }}"

    @memoized.memoized_method
    def get_object(self):
        jb_id = self.kwargs["job_binary_id"]
        try:
            return saharaclient.job_binary_get(self.request, jb_id)
        except Exception:
            msg = _('Unable to retrieve details for job binary "%s".') % jb_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(JobBinaryDetailsView, self).get_context_data(**kwargs)
        job_binary = self.get_object()
        context['job_binary'] = job_binary
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(job_binary)
        return context

    def _get_actions(self, job_binary):
        table = jb_tables.JobBinariesTable(self.request)
        return table.render_row_actions(job_binary)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing.jobs:index")


class DownloadJobBinaryView(django.views.generic.View):
    def get(self, request, job_binary_id=None):
        try:
            jb = saharaclient.job_binary_get(request, job_binary_id)
            data = saharaclient.job_binary_get_file(request, job_binary_id)
        except Exception:
            redirect = reverse(
                'horizon:project:data_processing.jobs:index')
            exceptions.handle(self.request,
                              _('Unable to fetch job binary: %(exc)s'),
                              redirect=redirect)
        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = (
            'attachment; filename="%s"' % jb.name)
        response.write(data)
        response['Content-Length'] = str(len(data))
        return response
