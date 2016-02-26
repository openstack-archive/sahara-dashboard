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

from openstack_dashboard.test.integration_tests import helpers
from openstack_dashboard.test.integration_tests.regions import messages


IMAGE_NAME = helpers.gen_random_resource_name("image")


class TestSaharaImageRegistry(helpers.TestCase):

    def setUp(self):
        super(TestSaharaImageRegistry, self).setUp()
        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.create_image(IMAGE_NAME)
        image_pg.find_message_and_dismiss(messages.SUCCESS)
        image_pg.wait_until_image_active(IMAGE_NAME)

    def test_image_register_unregister(self):
        """Test the image registration in Sahara."""
        image_reg_pg = \
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage()
        image_reg_pg.register_image(IMAGE_NAME, self.CONFIG.scenario.ssh_user,
                                    "Test description")
        image_reg_pg.wait_until_image_registered(IMAGE_NAME)
        self.assertTrue(image_reg_pg.is_image_registered(IMAGE_NAME),
                        "Image was not registered.")
        self.assertTrue(
            image_reg_pg.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            image_reg_pg.find_message_and_dismiss(messages.ERROR),
            "Error message occurred during image creation.")

        image_reg_pg.unregister_image(IMAGE_NAME)
        self.assertTrue(
            image_reg_pg.find_message_and_dismiss(messages.SUCCESS))
        self.assertFalse(
            image_reg_pg.find_message_and_dismiss(messages.ERROR))
        self.assertFalse(image_reg_pg.is_image_registered(IMAGE_NAME),
                         "Image was not unregistered.")

    def tearDown(self):
        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.delete_image(IMAGE_NAME)
        super(TestSaharaImageRegistry, self).tearDown()
