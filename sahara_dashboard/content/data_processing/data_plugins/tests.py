# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from unittest import mock

from django.urls import reverse

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test
from sahara_dashboard.test.helpers import IsHttpRequest


INDEX_URL = reverse(
    'horizon:project:data_processing.data_plugins:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.data_plugins:plugin-details', args=['id'])


class DataProcessingPluginsTests(test.TestCase):

    @test.create_mocks({api.sahara: ('plugin_list',)})
    def test_index(self):
        self.mock_plugin_list.return_value = self.plugins.list()
        res = self.client.get(INDEX_URL)
        self.mock_plugin_list.assert_called_once_with(IsHttpRequest())
        self.assertTemplateUsed(res, 'data_plugins/plugins.html')
        self.assertContains(res, 'vanilla')
        self.assertContains(res, 'plugin')

    @test.create_mocks({api.sahara: ('plugin_get',)})
    def test_details(self):
        self.mock_plugin_get.return_value = self.plugins.list()[0]
        res = self.client.get(DETAILS_URL)
        self.assert_mock_multiple_calls_with_same_arguments(
            self.mock_plugin_get, 2, mock.call(test.IsHttpRequest(),
                                               test.IsA(str)))
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'vanilla')
        self.assertContains(res, 'plugin')
