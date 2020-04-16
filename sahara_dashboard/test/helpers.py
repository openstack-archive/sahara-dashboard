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

from unittest import mock

from openstack_dashboard.test import helpers

from sahara_dashboard import api
from sahara_dashboard.test.test_data import utils

# Shortcuts to avoid importing openstack_dashboard.test.helper and
# for backwards compatibility.
create_mocks = helpers.create_mocks
IsA = helpers.IsA
IsHttpRequest = helpers.IsHttpRequest


class SaharaTestsMixin(object):
    def _setup_test_data(self):
        super(SaharaTestsMixin, self)._setup_test_data()
        utils.load_test_data(self)
        self.policy_patcher = mock.patch(
            'openstack_auth.policy.check', lambda action, request: True)
        self.policy_check = self.policy_patcher.start()


class TestCase(SaharaTestsMixin, helpers.TestCase):
    pass


class BaseAdminViewTests(SaharaTestsMixin, helpers.TestCase):
    pass


class SaharaAPITestCase(helpers.APITestCase):

    def setUp(self):
        super(SaharaAPITestCase, self).setUp()

        self._original_saharaclient = api.sahara.client
        api.sahara.client = lambda request: self.stub_saharaclient()

    def tearDown(self):
        super(SaharaAPITestCase, self).tearDown()

        api.sahara.client = self._original_saharaclient

    def stub_saharaclient(self):
        if not hasattr(self, "saharaclient"):
            self.saharaclient = mock.Mock()
        return self.saharaclient
