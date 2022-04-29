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

from django.urls import re_path

import sahara_dashboard.content.data_processing. \
    jobs.views as views
import sahara_dashboard.content.data_processing. \
    jobs.job_binaries.views as job_binary_views
import sahara_dashboard.content.data_processing. \
    jobs.data_sources.views as data_source_views
import sahara_dashboard.content.data_processing. \
    jobs.job_templates.views as job_templates_views
import sahara_dashboard.content.data_processing. \
    jobs.wizard.views as job_wizard_views
import sahara_dashboard.content.data_processing. \
    jobs.jobs.views as jobs_views


urlpatterns = [re_path(r'^$', views.IndexView.as_view(), name='index'),
               re_path(r'^$', views.IndexView.as_view(), name='jobs'),
               re_path(r'^\?tab=job_tabs__jobs_tab$',
                       views.IndexView.as_view(),
                       name='jobs-tab'),
               re_path(r'^create-job$',
                       job_templates_views.CreateJobView.as_view(),
                       name='create-job'),
               re_path(r'^launch-job$',
                       job_templates_views.LaunchJobView.as_view(),
                       name='launch-job'),
               re_path(r'^launch-job-new-cluster$', job_templates_views.
                       LaunchJobNewClusterView.as_view(),
                       name='launch-job-new-cluster'),
               re_path(r'^choose-plugin$',
                       job_templates_views.ChoosePluginView.as_view(),
                       name='choose-plugin'),
               re_path(r'^job-template/(?P<job_id>[^/]+)$',
                       job_templates_views.
                       JobTemplateDetailsView.as_view(), name='jt-details'),
               re_path(r'^job-execution/(?P<job_execution_id>[^/]+)$',
                       jobs_views.JobDetailsView.as_view(), name='details'),
               re_path(r'^create-job-binary$',
                       job_binary_views.CreateJobBinaryView.as_view(),
                       name='create-job-binary'),
               re_path(r'^job-binary/(?P<job_binary_id>[^/]+)$',
                       job_binary_views.JobBinaryDetailsView.as_view(),
                       name='jb-details'),
               re_path(r'^job-binary/(?P<job_binary_id>[^/]+)/edit$',
                       job_binary_views.EditJobBinaryView.as_view(),
                       name='edit-job-binary'),
               re_path(r'^job-binary/(?P<job_binary_id>[^/]+)/download/$',
                       job_binary_views.DownloadJobBinaryView.as_view(),
                       name='download'),
               re_path(r'^create-data-source$',
                       data_source_views.CreateDataSourceView.as_view(),
                       name='create-data-source'),
               re_path(r'^data-source/(?P<data_source_id>[^/]+)/edit$',
                       data_source_views.EditDataSourceView.as_view(),
                       name='edit-data-source'),
               re_path(r'^data-source/(?P<data_source_id>[^/]+)$',
                       data_source_views.DataSourceDetailsView.as_view(),
                       name='ds-details'),
               re_path(r'^jobex_guide$',
                       job_wizard_views.JobExecutionGuideView.as_view(),
                       name='jobex_guide'),
               re_path(r'^jobex_guide/(?P<reset_jobex_guide>[^/]+)/$',
                       job_wizard_views.ResetJobExGuideView.as_view(),
                       name='reset_jobex_guide'),
               re_path(r'^job_type_select$',
                       job_wizard_views.JobTypeSelectView.as_view(),
                       name='job_type_select'),
               ]
