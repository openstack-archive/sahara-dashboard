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

from django.core.urlresolvers import reverse
from django import http
from mox3.mox import IsA  # noqa
import six

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test

INDEX_URL = reverse('horizon:project:data_processing.jobs:index')
DETAILS_URL = reverse(
    'horizon:project:data_processing.jobs:ds-details', args=['id'])
CREATE_URL = reverse(
    'horizon:project:data_processing.jobs:create-data-source')
EDIT_URL = reverse(
    'horizon:project:data_processing.jobs:edit-data-source',
    args=['id'])


class DataProcessingDataSourceTests(test.TestCase):
    @test.create_stubs({api.sahara: ('data_source_list',)})
    def test_index(self):
        api.sahara.data_source_list(IsA(http.HttpRequest)) \
            .AndReturn(self.data_sources.list())
        self.mox.ReplayAll()
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(res, 'jobs/index.html')
        self.assertContains(res, 'Data Sources')
        self.assertContains(res, 'Name')
        self.assertContains(res, 'sampleOutput')
        self.assertContains(res, 'sampleOutput2')

    @test.create_stubs({api.sahara: ('data_source_get',)})
    def test_details(self):
        api.sahara.data_source_get(IsA(http.HttpRequest), IsA(six.text_type)) \
            .MultipleTimes().AndReturn(self.data_sources.first())
        self.mox.ReplayAll()
        res = self.client.get(DETAILS_URL)
        self.assertTemplateUsed(res, 'horizon/common/_detail.html')
        self.assertContains(res, 'sampleOutput')

    @test.create_stubs({api.sahara: ('data_source_list',
                                     'data_source_delete')})
    def test_delete(self):
        data_source = self.data_sources.first()
        api.sahara.data_source_list(IsA(http.HttpRequest)) \
            .AndReturn(self.data_sources.list())
        api.sahara.data_source_delete(IsA(http.HttpRequest), data_source.id)
        self.mox.ReplayAll()

        form_data = {'action': 'data_sources__delete__%s' % data_source.id}
        res = self.client.post(INDEX_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('data_source_create',)})
    def test_create(self):
        data_source = self.data_sources.first()
        api.sahara.data_source_create(IsA(http.HttpRequest),
                                      data_source.name,
                                      data_source.description,
                                      data_source.type,
                                      data_source.url,
                                      "",
                                      "",
                                      is_public=False,
                                      is_protected=False) \
            .AndReturn(self.data_sources.first())
        self.mox.ReplayAll()
        form_data = {
            'data_source_url': data_source.url,
            'data_source_name': data_source.name,
            'data_source_description': data_source.description,
            'data_source_type': data_source.type,
            'is_public': False,
            'is_protected': False,
        }
        res = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.sahara: ('data_source_update',
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
        api.sahara.data_source_get(IsA(http.HttpRequest),
                                   IsA(six.text_type)) \
            .AndReturn(self.data_sources.first())
        api.sahara.data_source_update(IsA(http.HttpRequest),
                                      IsA(six.text_type),
                                      api_data) \
            .AndReturn(self.data_sources.first())
        self.mox.ReplayAll()

        form_data = {
            'data_source_url': data_source.url,
            'data_source_name': data_source.name,
            'data_source_description': data_source.description,
            'data_source_type': data_source.type,
        }
        res = self.client.post(EDIT_URL, form_data)

        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_stubs({api.manila: ('share_list', ),
                        api.sahara: ('data_source_create', ),
                        api.sahara.base: ('is_service_enabled', )})
    def test_create_manila(self):
        share = self.mox.CreateMockAnything()
        share.id = "tuvwxy56-1234-abcd-abcd-defabcdaedcb"
        share.name = "Test Share"
        shares = [share]
        api.sahara.base.is_service_enabled(IsA(http.HttpRequest), IsA(str)) \
            .AndReturn(True)
        api.sahara.data_source_create(IsA(http.HttpRequest),
                                      IsA(six.text_type),
                                      IsA(six.text_type),
                                      IsA(six.text_type),
                                      IsA(str),
                                      "", "", is_public=False,
                                      is_protected=False).AndReturn(True)
        api.manila.share_list(IsA(http.HttpRequest)).AndReturn(shares)
        self.mox.ReplayAll()

        form_data = {
            "data_source_type": "manila",
            "data_source_manila_share": share.id,
            "data_source_url": "/testfile.bin",
            "data_source_name": "testmanila",
            "data_source_description": "Test manila description",
        }

        res = self.client.post(CREATE_URL, form_data)
        self.assertNoFormErrors(res)
