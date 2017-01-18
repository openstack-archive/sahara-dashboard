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

from oslo_log import log as logging

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from sahara_dashboard.api import sahara as saharaclient
from sahara_dashboard.content.data_processing.jobs.job_binaries \
    import tables as job_binary_tables
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs

LOG = logging.getLogger(__name__)


class JobBinariesTab(sahara_tabs.SaharaTableTab):
    table_classes = (job_binary_tables.JobBinariesTable, )
    name = _("Job Binaries")
    slug = "job_binaries_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_job_binaries_data(self):
        try:
            job_binaries = saharaclient.job_binary_list(self.request)
        except Exception:
            job_binaries = []
            exceptions.handle(self.request,
                              _("Unable to fetch job binary list"))
        return job_binaries


class JobBinaryDetailsTab(tabs.Tab):
    name = _("General Info")
    slug = "job_binaries_details_tab"
    template_name = "job_binaries/_details.html"

    def get_context_data(self, request):
        job_binary_id = self.tab_group.kwargs['job_binary_id']
        try:
            job_binary = saharaclient.job_binary_get(request, job_binary_id)
        except Exception as e:
            job_binary = {}
            LOG.error("Unable to fetch job binary details: %s" % str(e))
        return {"job_binary": job_binary}


class JobBinaryDetailsTabs(tabs.TabGroup):
    slug = "job_binary_details"
    tabs = (JobBinaryDetailsTab,)
    sticky = True
