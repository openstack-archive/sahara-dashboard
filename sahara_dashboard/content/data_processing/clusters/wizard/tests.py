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

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test


CLUSTER_GUIDE_URL = reverse(
    'horizon:project:data_processing.clusters:cluster_guide')
CLUSTER_GUIDE_RESET_URL = reverse(
    'horizon:project:data_processing.clusters:reset_cluster_guide',
    kwargs={"reset_cluster_guide": "true"})


class DataProcessingClusterGuideTests(test.TestCase):

    @test.create_mocks({api.sahara: ('nodegroup_template_find',)})
    def test_cluster_guide(self):
        res = self.client.get(CLUSTER_GUIDE_URL)
        self.assertTemplateUsed(
            res, 'cluster_wizard/cluster_guide.html')
        self.assertContains(res, 'Guided Cluster Creation')
        self.assertContains(res, 'Current choice')

    def test_cluster_guide_reset(self):
        res = self.client.get(CLUSTER_GUIDE_RESET_URL)
        self.assertRedirectsNoFollow(res, CLUSTER_GUIDE_URL)
