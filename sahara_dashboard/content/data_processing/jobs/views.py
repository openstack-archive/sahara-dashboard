# Copyright 2016 Rec Hat Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from sahara_dashboard.content.data_processing.jobs.data_sources \
    import tabs as data_source_tabs
from sahara_dashboard.content.data_processing.jobs.job_binaries \
    import tabs as job_binary_tabs
from sahara_dashboard.content.data_processing.jobs.job_templates \
    import tabs as job_template_tabs
from sahara_dashboard.content.data_processing.jobs.jobs \
    import tabs as job_tabs
from sahara_dashboard.content.data_processing.tabs \
    import PaginationFriendlyTabGroup


class JobTabs(PaginationFriendlyTabGroup):
    slug = "job_tabs"
    tabs = (job_tabs.JobsTab,
            job_template_tabs.JobTemplatesTab,
            data_source_tabs.DataSourcesTab,
            job_binary_tabs.JobBinariesTab,)
    sticky = True


class IndexView(tabs.TabbedTableView):
    tab_group_class = JobTabs
    template_name = "jobs/index.html"
    page_title = _("Jobs")
