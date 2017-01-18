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
from sahara_dashboard.content.data_processing \
    import tabs as sahara_tabs
from sahara_dashboard.content.data_processing.jobs \
    .job_templates import tables as job_templates_tables

LOG = logging.getLogger(__name__)


class JobTemplatesTab(sahara_tabs.SaharaTableTab):
    table_classes = (job_templates_tables.JobTemplatesTable, )
    name = _("Job Templates")
    slug = "job_templates_tab"
    template_name = "horizon/common/_detail_table.html"

    def get_job_templates_data(self):
        try:
            table = self._tables['job_templates']
            search_opts = {}
            filter = self.get_server_filter_info(table.request, table)
            if filter['value'] and filter['field']:
                search_opts = {filter['field']: filter['value']}
            job_templates = saharaclient.job_list(self.request, search_opts)
        except Exception:
            job_templates = []
            exceptions.handle(self.request,
                              _("Unable to fetch job template list"))
        return job_templates


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_details_tab"
    template_name = "job_templates/_details.html"

    def get_context_data(self, request):
        job_id = self.tab_group.kwargs['job_id']
        try:
            job = saharaclient.job_get(request, job_id)
        except Exception as e:
            job = {}
            LOG.error("Unable to fetch job template details: %s" % str(e))
        return {"job": job}


class JobDetailsTabs(tabs.TabGroup):
    slug = "job_details"
    tabs = (GeneralTab,)
    sticky = True
