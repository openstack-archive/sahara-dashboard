# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.urls import reverse

from sahara_dashboard.test import helpers as test


JOB_GUIDE_URL = reverse(
    'horizon:project:data_processing.jobs:jobex_guide')
JOB_GUIDE_RESET_URL = reverse(
    'horizon:project:data_processing.jobs:reset_jobex_guide',
    kwargs={"reset_jobex_guide": "true"})


class DataProcessingClusterGuideTests(test.TestCase):
    def test_jobex_guide(self):
        res = self.client.get(JOB_GUIDE_URL)
        self.assertTemplateUsed(
            res, 'job_wizard/jobex_guide.html')
        self.assertContains(res, 'Guided Job Execution')

    def test_jobex_guide_reset(self):
        res = self.client.get(JOB_GUIDE_RESET_URL)
        self.assertRedirectsNoFollow(res, JOB_GUIDE_URL)
