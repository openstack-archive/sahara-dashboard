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

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
from horizon.utils import memoized

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.jobs.jobs \
    import tables as je_tables
import sahara_dashboard.content.data_processing \
    .jobs.jobs.tabs as _tabs


class JobDetailsView(tabs.TabView):
    tab_group_class = _tabs.JobExecutionDetailsTabs
    template_name = 'horizon/common/_detail.html'
    page_title = "{{ job_execution.name|default:job_execution.id }}"

    @memoized.memoized_method
    def get_object(self):
        jex_id = self.kwargs["job_execution_id"]
        try:
            return saharaclient.job_execution_get(self.request, jex_id)
        except Exception:
            msg = _('Unable to retrieve details for job "%s".') % jex_id
            redirect = self.get_redirect_url()
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_context_data(self, **kwargs):
        context = super(JobDetailsView, self)\
            .get_context_data(**kwargs)
        job_execution = self.get_object()
        context['job_execution'] = job_execution
        context['url'] = self.get_redirect_url()
        context['actions'] = self._get_actions(job_execution)
        return context

    def _get_actions(self, job_execution):
        table = je_tables.JobsTable(self.request)
        return table.render_row_actions(job_execution)

    @staticmethod
    def get_redirect_url():
        return reverse("horizon:project:data_processing.jobs:jobs-tab")
