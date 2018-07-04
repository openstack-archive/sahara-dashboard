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

from django.urls import reverse

from openstack_dashboard import api as dash_api

from sahara_dashboard import api
from sahara_dashboard.test import helpers as test
from sahara_dashboard.test.helpers import IsHttpRequest

INDEX_URL = reverse(
    'horizon:project:data_processing.clusters:image-registry-tab')
REGISTER_URL = reverse(
    'horizon:project:data_processing.clusters:register')
SUCCESS_URL = reverse(
    'horizon:project:data_processing.clusters:index')


class DataProcessingImageRegistryTests(test.TestCase):

    @test.create_mocks({api.sahara: ('cluster_template_list',
                                     'image_list',
                                     'cluster_list',
                                     'nodegroup_template_list')})
    def test_index(self):
        self.mock_image_list.return_value = self.images.list()

        res = self.client.get(INDEX_URL)

        self.mock_image_list.assert_called_once_with(
            IsHttpRequest())
        self.assertTemplateUsed(res, 'clusters/index.html')
        self.assertContains(res, 'Image Registry')
        self.assertContains(res, 'Image')
        self.assertContains(res, 'Tags')

    @test.create_mocks({api.sahara: ('image_get',
                                     'image_update',
                                     'image_tags_update',
                                     'image_list'),
                        dash_api.glance: ('image_list_detailed',)})
    def test_register(self):
        image = self.images.first()
        image_id = image.id
        test_username = 'myusername'
        test_description = 'mydescription'
        self.mock_image_get.return_value = image
        self.mock_image_list_detailed.return_value = (
            self.images.list(), False, False)
        self.mock_image_update.return_value = True
        self.mock_image_tags_update.return_value = True
        self.mock_image_list.return_value = []

        res = self.client.post(
            REGISTER_URL,
            {'image_id': image_id,
             'user_name': test_username,
             'description': test_description,
             'tags_list': '{}'})

        self.mock_image_list_detailed.assert_called_once_with(
            IsHttpRequest(),
            filters={'owner': self.user.id,
                     'status': 'active'})
        self.mock_image_update.assert_called_once_with(
            IsHttpRequest(), image_id, test_username, test_description)
        self.mock_image_tags_update.assert_called_once_with(
            IsHttpRequest(), image_id, {})
        self.mock_image_list.assert_called_once_with(
            IsHttpRequest())
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, SUCCESS_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.sahara: ('image_list',
                                     'image_unregister')})
    def test_unregister(self):
        image = self.images.first()
        self.mock_image_list.return_value = self.images.list()
        self.mock_image_unregister.return_value = None

        form_data = {'action': 'image_registry__unregister__%s' % image.id}
        res = self.client.post(INDEX_URL, form_data)

        self.mock_image_list.assert_called_once_with(
            IsHttpRequest())
        self.mock_image_unregister.assert_called_once_with(
            IsHttpRequest(), image.id)
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, INDEX_URL)
        self.assertMessageCount(success=1)

    @test.create_mocks({api.sahara: ('image_get',
                                     'image_update',
                                     'image_tags_update')})
    def test_edit_tags(self):
        image = self.registered_images.first()
        self.mock_image_get.return_value = image
        self.mock_image_update.return_value = True
        self.mock_image_tags_update.return_value = True

        edit_tags_url = reverse(
            'horizon:project:data_processing.clusters:edit_tags',
            args=[image.id])
        res = self.client.post(
            edit_tags_url,
            {'image_id': image.id,
             'user_name': image.username,
             'description': image.description,
             'tags_list': '{"0": "mytag"}'})

        self.mock_image_update.assert_called_once_with(
            IsHttpRequest(), image.id, image.username,
            image.description)
        self.mock_image_tags_update.assert_called_once_with(
            IsHttpRequest(), image.id, {"0": "mytag"})
        self.assertNoFormErrors(res)
        self.assertRedirectsNoFollow(res, SUCCESS_URL)
        self.assertMessageCount(success=1)
