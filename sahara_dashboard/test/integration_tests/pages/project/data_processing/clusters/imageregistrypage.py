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

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class ImageRegistryTable(tables.TableRegion):
    name = "image_registry"
    REGISTER_FORM_FIELDS = ('image_id', 'user_name', 'description')

    @tables.bind_table_action('register')
    def register_image(self, register_button):
        register_button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.REGISTER_FORM_FIELDS)

    @tables.bind_table_action('unregister')
    def unregister_image(self, unregister_button):
        unregister_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class ImageregistryPage(basepage.BaseNavigationPage):

    TABLE_IMAGE_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(ImageregistryPage, self).__init__(driver, conf)
        self._page_title = "Clusters"

    def _get_row_with_image_name(self, name):
        return self.image_table.get_row(self.TABLE_IMAGE_COLUMN, name)

    @property
    def image_table(self):
        return ImageRegistryTable(self.driver, self.conf)

    def is_image_registered(self, name):
        return bool(self._get_row_with_image_name(name))

    def unregister_image(self, name):
        self._get_row_with_image_name(name).mark()
        unregister_form = self.image_table.unregister_image()
        unregister_form.submit()

    def register_image(self, image, user_name, description, tags=()):
        register_form = self.image_table.register_image()
        register_form.image_id.text = image
        register_form.user_name.text = user_name
        register_form.description.text = description
        tag_input = register_form.src_elem.find_element_by_id(
            "_sahara_image_tag")
        tag_add_btn = register_form.src_elem.find_element_by_id("add_tag_btn")
        for tag in tags:
            tag_input.send_keys(tag)
            tag_add_btn.click()
        register_form.submit()

    def wait_until_image_registered(self, name):
        self._wait_until(lambda x: self.is_image_registered(name))
