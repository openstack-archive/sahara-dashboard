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

from datetime import datetime

from oslo_config import cfg

from openstack_dashboard.test.integration_tests import helpers


class SaharaTestCase(helpers.AdminTestCase):

    @classmethod
    def setUpClass(cls):
        sahara_group = cfg.OptGroup(
            'sahara', help='Sahara specific tests config group')
        cls.CONFIG.register_group(sahara_group)
        fake_image_location = cfg.StrOpt('fake_image_location')
        cls.CONFIG.register_opt(fake_image_location, group=sahara_group)
        ssh_user = cfg.StrOpt('fake_image_ssh_user')
        cls.CONFIG.register_opt(ssh_user, group=sahara_group)
        project_name = cfg.StrOpt('project_name', default='demo')
        cls.CONFIG.register_opt(project_name, group=sahara_group)
        ip_pool = cfg.StrOpt('ip_pool', default="public")
        cls.CONFIG.register_opt(ip_pool, group=sahara_group)
        launch_timeout = cfg.IntOpt('launch_timeout', default=1200)
        cls.CONFIG.register_opt(launch_timeout, group=sahara_group)

        flavor_vcpus = cfg.IntOpt('flavor_vcpus', default=1)
        cls.CONFIG.register_opt(flavor_vcpus, group=sahara_group)
        flavor_ram = cfg.IntOpt('flavor_ram', default=256)
        cls.CONFIG.register_opt(flavor_ram, group=sahara_group)
        flavor_root_disk = cfg.IntOpt('flavor_root_disk', default=3)
        cls.CONFIG.register_opt(flavor_root_disk, group=sahara_group)
        flavor_ephemeral_disk = cfg.IntOpt('flavor_ephemeral_disk', default=0)
        cls.CONFIG.register_opt(flavor_ephemeral_disk, group=sahara_group)
        flavor_swap_disk = cfg.IntOpt('flavor_swap_disk', default=0)
        cls.CONFIG.register_opt(flavor_swap_disk, group=sahara_group)

    def setUp(self):
        super(SaharaTestCase, self).setUp()
        self._suffix = datetime.now().strftime('%H-%M-%S-%f')[:12]
        # select project
        driver = self.home_pg.driver
        driver.find_element_by_css_selector('li.dropdown').click()
        driver.find_element_by_link_text(
            self.CONFIG.sahara.project_name).click()

    def gen_name(self, name):
        return '{}-{}'.format(name, self._suffix)
