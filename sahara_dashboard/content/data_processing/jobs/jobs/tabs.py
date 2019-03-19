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
from sahara_dashboard.content.data_processing \
    .jobs.jobs import tables as jobs_tables

LOG = logging.getLogger(__name__)


class JobsTab(sahara_tabs.SaharaTableTab):
    table_classes = (jobs_tables.JobsTable, )
    name = _("Jobs")
    slug = "jobs_tab"
    template_name = "horizon/common/_detail_table.html"
    SEARCH_MAPPING = {"cluster": "cluster.name",
                      "job": "job.name"}

    def get_jobs_data(self):
        try:
            table = self._tables['jobs']
            search_opts = {}
            filter = self.get_server_filter_info(table.request, table)
            if filter['value'] and filter['field']:
                if filter['field'] in self.SEARCH_MAPPING:
                    # Handle special cases for cluster and job
                    # since they are in different database tables.
                    search_opts = {
                        self.SEARCH_MAPPING[filter['field']]: filter['value']}
                else:
                    search_opts = {filter['field']: filter['value']}
            jobs = saharaclient.job_execution_list(self.request, search_opts)
        except Exception:
            jobs = []
            exceptions.handle(self.request,
                              _("Unable to fetch job list"))
        return jobs


class GeneralTab(tabs.Tab):
    name = _("General Info")
    slug = "job_execution_tab"
    template_name = "jobs/_details.html"

    def get_context_data(self, request):
        jex_id = self.tab_group.kwargs['job_execution_id']
        try:
            job_execution = saharaclient.job_execution_get(request, jex_id)
        except Exception as e:
            job_execution = {}
            LOG.error("Unable to fetch job details: %s" % str(e))
            return {"job_execution": job_execution}
        object_names = self.get_object_names(job_execution,
                                             request)
        try:
            object_names['input_url'] = job_execution.data_source_urls.get(
                job_execution.input_id)
        except Exception as e:
            LOG.error("Unable to fetch input url: %s", e)
            object_names["input_url"] = "None"

        try:
            object_names['output_url'] = job_execution.data_source_urls.get(
                job_execution.output_id)
        except Exception as e:
            LOG.error("Unable to fetch output url: %s", e)
            object_names["output_url"] = "None"

        if saharaclient.VERSIONS.active == '2':
            job_execution_engine_job_attr = "engine_job_id"
            job_execution_engine_job_attr_pretty = _("Engine Job ID")
        else:
            job_execution_engine_job_attr = "oozie_job_id"
            job_execution_engine_job_attr_pretty = _("Oozie Job ID")

        job_execution_engine_job_id = getattr(job_execution,
                                              job_execution_engine_job_attr)

        return {"job_execution": job_execution,
                "object_names": object_names,
                "job_execution_engine_job_id": job_execution_engine_job_id,
                "job_execution_engine_job_attr_pretty":
                    job_execution_engine_job_attr_pretty}

    def get_object_names(self, job_ex, request):
        object_names = {}
        try:
            job_template_id = job_ex.job_template_id  # typical APIv2
        except AttributeError:
            job_template_id = job_ex.job_id  # APIv1.1, older APIv2
        obj_names_map = {'input_name': {'obj': 'data_source_get',
                                        'obj_id': job_ex.input_id},
                         'output_name': {'obj': 'data_source_get',
                                         'obj_id': job_ex.output_id},
                         'cluster_name': {'obj': 'cluster_get',
                                          'obj_id': job_ex.cluster_id},
                         'job_name': {'obj': 'job_get',
                                      'obj_id': job_template_id}}
        for item in obj_names_map:
            object_names[item] = (
                self.get_object_name(obj_names_map[item]['obj_id'],
                                     obj_names_map[item]['obj'],
                                     request))

        return object_names

    def get_object_name(self, obj_id, sahara_obj, request):
        object_name = None
        try:
            s_func = getattr(saharaclient, sahara_obj)
            obj = s_func(request, obj_id)
            object_name = obj.name
        except Exception as e:
            LOG.warning("Unable to get name for %s with object_id %s (%s)"
                        % (sahara_obj, obj_id, str(e)))
        return object_name


class JobExecutionDetailsTabs(tabs.TabGroup):
    slug = "job_details"
    tabs = (GeneralTab,)
    sticky = True
