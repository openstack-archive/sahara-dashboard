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

from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables

from sahara_dashboard.test.integration_tests.pages import basepage
from sahara_dashboard.test.integration_tests.pages import mixins


class CreateMixin(object):
    CREATE_FIELD_MAPPING = (
        "data_source_name",
        "data_source_type",
        "data_source_url",
        "data_source_credential_user",
        "data_source_credential_pass",
        "data_source_description"
    )

    @tables.bind_table_action('create data source')
    def get_create_form(self, button):
        button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_FIELD_MAPPING)

    @tables.bind_row_action('edit data source')
    def get_update_form(self, button, row):
        button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.CREATE_FIELD_MAPPING)


class DatasourcesPage(mixins.DeleteMixin, basepage.BaseDataProcessingPage):

    TABLE_NAME = "data_sources"

    @classmethod
    def get_table_mixins(cls):
        return super(DatasourcesPage, cls).get_table_mixins() + (CreateMixin,)

    def create(self, name, source_type, url):
        form = self.table.get_create_form()
        form.data_source_name.text = name
        form.data_source_type.text = source_type
        form.data_source_url.text = url
        form.submit()

    def update(self, name, **kwargs):
        row = self._get_row_with_name(name)
        form = self.table.get_update_form(row)
        for key in CreateMixin.CREATE_FIELD_MAPPING:
            if key in kwargs:
                getattr(form, key).text = kwargs[key]
        form.submit()

    def get_details(self, name):
        details = {}
        self.table.src_elem.find_element_by_link_text(name).click()
        items = self.driver.find_elements_by_css_selector('div.detail dt')
        for item in items:
            key = item.text
            value_elem = item.find_element_by_xpath('./following-sibling::*')
            if value_elem.tag_name != "dd":
                continue
            value = value_elem.text
            details[key] = value
        return details
