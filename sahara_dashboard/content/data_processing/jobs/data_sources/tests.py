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
from sahara_dashboard.test.helpers import IsA
from sahara_dashboard.test.helpers import IsHttpRequest

INDEX_URL = reverse('horizon:project:data_processing.jobs:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.jobs:ds-details', args=['id'])
CREATE_URL = reverse(
    'horizon:project:data_processing.jobs:create-data-source')
EDIT_URL = reverse(
    'horizon:project:data_processing.jobs:edit-data-source',
    args=['id'])


class DataProcessingDataSourceTests(test.TestCase):

    @test.create_mocks({api.sahara: ('job_execution_list',
                                     'plugin_list', 'job_binary_list',
                                     'data_source_list',
                                     'job_list')})
    def test_index(self):
        self.mock_data_source_list.return_value = self.data_sources.list()
        res = self.client.get(INDEX_URL)
        self.mock_data_source_list.assert_called_once_with(
            IsHttpRequest())
        self.assertTemplateUsed(res, 'jobs/index.html')
        self.assertContains(res, 'Data Sources')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'sampleOutput')
        self.assertContains(res, 'sampleOutput2')

    @test.create_mocks({api.sahara: ('data_source_get',)})
    def test_details(self):
        self.mock_data_source_get.return_value = self.data_sources.first()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'sampleOutput')

    @test.create_mocks({api.sahara: ('data_source_list',
                                     'data_source_delete')})
    def test_delete(self):
        data_source = self.data_sources.first()
        self.mock_data_source_list.return_value = self.data_sources.list()
        self.mock_data_source_delete.return_value = None

        form_data = {'action': 'data_sources__delete__%s' % data_source.id}
        res = self.client.post(INDEX_URL, form_data)

        self.mock_data_source_list.assert_called_once_with(
            IsHttpRequest())
        self.mock_data_source_delete.assert_called_once_with(
            IsHttpRequest(), data_source.id)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.sahara: ('data_source_create',)})
    def test_create(self):
        data_source = self.data_sources.first()
        self.mock_data_source_create.return_value = \
            self.data_sources.first()
        form_data = {
            'data_source_url': data_source.url,
            'data_source_name': data_source.name,
            'data_source_description': data_source.description,
            'data_source_type': data_source.type,
            'is_public': False,
            'is_protected': False,
        }
        res = self.client.post(CREATE_URL, form_data)

        self.mock_data_source_create.assert_called_once_with(
            IsHttpRequest(),
            data_source.name,
            data_source.description,
            data_source.type,
            data_source.url,
            '',
            '',
            is_public=False,
            is_protected=False,
            s3_credentials=None)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.sahara: ('data_source_update',
                                     'data_source_get',)})
    def test_edit(self):
        data_source = self.data_sources.first()
        api_data = {
            'url': data_source.url,
            'credentials': {'user': '', 'password': ''},
            'type': data_source.type,
            'name': data_source.name,
            'description': data_source.description,
            'is_public': False,
            'is_protected': False,
        }
        self.mock_data_source_get.return_value = self.data_sources.first()
        self.mock_data_source_update.return_value = self.data_sources.first()

        form_data = {
            'data_source_url': data_source.url,
            'data_source_name': data_source.name,
            'data_source_description': data_source.description,
            'data_source_type': data_source.type,
        }
        res = self.client.post(EDIT_URL, form_data)

        self.mock_data_source_get.assert_called_once_with(
            IsHttpRequest(), IsA(str))
        self.mock_data_source_update.assert_called_once_with(
            IsHttpRequest(), IsA(str), api_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.manila: ('share_list', ),
                        api.sahara: ('data_source_create', ),
                        api.sahara.base: ('is_service_enabled', )})
    def test_create_manila(self):
        share = mock.Mock()
        share.return_value = {
            'id': 'tuvwxy56-1234-abcd-abcd-defabcdaedcb',
            'name': 'Test Share'
        }
        shares = [share]
        self.mock_is_service_enabled.return_value = True
        self.mock_data_source_create.return_value = True
        self.mock_share_list.return_value = shares

        form_data = {
            "data_source_type": "manila",
            "data_source_manila_share": share.id,
            "data_source_url": "/testfile.bin",
            "data_source_name": "testmanila",
            "data_source_description": "Test manila description",
        }

        res = self.client.post(CREATE_URL, form_data)
        self.mock_is_service_enabled.assert_called_once_with(
            IsHttpRequest(), IsA(str))
        self.mock_data_source_create.assert_called_once_with(
            IsHttpRequest(),
            IsA(str),
            IsA(str),
            IsA(str),
            IsA(str),
            '', '', is_public=False, is_protected=False, s3_credentials=None)
        self.mock_share_list.assert_called_once_with(IsHttpRequest())
        self.assertNoFormErrors(res)

    @test.create_mocks({api.sahara: ('data_source_create',)})
    def test_create_s3(self):
        form_data = {
            "data_source_type": "s3",
            "data_source_url": "s3a://a/b",
            "data_source_credential_accesskey": "acc",
            "data_source_credential_secretkey": "sec",
            "data_source_credential_endpoint": "pointy.end",
            "data_source_credential_s3_bucket_in_url": False,
            "data_source_credential_s3_ssl": True,
            "data_source_name": "tests3",
            "data_source_description": "Test s3 description"
        }
        res = self.client.post(CREATE_URL, form_data)
        self.mock_data_source_create.return_value = True
        self.mock_data_source_create.assert_called_once_with(
            IsHttpRequest(),
            IsA(str),
            IsA(str),
            IsA(str),
            IsA(str),
            IsA(str),
            IsA(str),
            is_public=False, is_protected=False, s3_credentials=IsA(dict))
        self.assertNoFormErrors(res)
