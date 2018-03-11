# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import http
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import forms
from horizon import views as horizon_views

import sahara_dashboard.content.data_processing.jobs.wizard.forms as wizforms
from sahara_dashboard.content.data_processing.utils \
    import helpers


class JobExecutionGuideView(horizon_views.APIView):
    template_name = 'job_wizard/jobex_guide.html'
    page_title = _("Guided Job Execution")

    def show_data_sources(self):
        try:
            if self.request.session["guide_job_type"] in ["Spark", "Storm",
                                                          "Storm.Pyleus"
                                                          "Java"]:
                return False
            return True
        except Exception:
            return True


class ResetJobExGuideView(generic.RedirectView):
    pattern_name = 'horizon:project:data_processing.jobs:jobex_guide'
    permanent = True

    def get(self, request, *args, **kwargs):
        if kwargs["reset_jobex_guide"]:
            hlps = helpers.Helpers(request)
            hlps.reset_job_guide()
        return http.HttpResponseRedirect(reverse_lazy(self.pattern_name))


class JobTypeSelectView(forms.ModalFormView):
    form_class = wizforms.ChooseJobTypeForm
    success_url = reverse_lazy(
        'horizon:project:data_processing.jobs:jobex_guide')
    classes = ("ajax-modal")
    template_name = "job_wizard/job_type_select.html"
    page_title = _("Choose job type")
