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
from openstack_dashboard.test.integration_tests.regions import messages
from openstack_dashboard.test.integration_tests.regions import tables


class JobBinariesTable(tables.TableRegion):
    name = 'job_binaries'
    CREATE_BINARY_FORM_FIELDS = (
        "job_binary_name",
        "job_binary_type",
        "job_binary_url",
        "job_binary_username",
        "job_binary_password",
        "job_binary_internal",
        "job_binary_file",
        "job_binary_script_name",
        "job_binary_script",
        "job_binary_description"
    )

    @tables.bind_table_action('create')
    def get_create_form(self, button):
        button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_BINARY_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def get_delete_form(self, button):
        button.click()
        return forms.BaseFormRegion(self.driver, self.conf)

    @tables.bind_row_action('edit_job_binary')
    def get_update_form(self, button, row):
        button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_BINARY_FORM_FIELDS)


class JobbinariesPage(basepage.BaseNavigationPage):

    JOB_BINARIES_TABLE_NAME_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(JobbinariesPage, self).__init__(driver, conf)
        self._page_title = "Data Processing"

    def _get_row_with_name(self, name):
        return self.table.get_row(
            self.JOB_BINARIES_TABLE_NAME_COLUMN, name)

    @property
    def table(self):
        return JobBinariesTable(self.driver, self.conf)

    def delete_job_binary(self, name):
        row = self._get_row_with_name(name)
        row.mark()
        confirm_delete_form = self.table.get_delete_form()
        confirm_delete_form.submit()

    def create_job_binary(self, binary_name, script_name):
        form = self.table.get_create_form()

        form.job_binary_name.text = binary_name
        form.job_binary_type.text = "Internal database"
        form.job_binary_internal.text = "*Create a script"
        form.job_binary_script_name.text = script_name
        form.job_binary_script.text = "test_script_text"
        form.job_binary_description.text = "test description"
        form.submit()

    def create_job_binary_from_file(self, binary_name, path):
        form = self.table.get_create_form()

        form.job_binary_name.text = binary_name
        form.job_binary_type.text = "Internal database"
        form.job_binary_internal.text = "*Upload a new file"
        form.job_binary_file.src_elem.send_keys(path)
        form.job_binary_description.text = "test description"
        form.submit()

    def update_job_binary(self, name, **kwargs):
        row = self._get_row_with_name(name)
        form = self.table.get_update_form(row)
        for key in JobBinariesTable.CREATE_BINARY_FORM_FIELDS:
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

    def is_job_binary_present(self, name):
        return bool(self._get_row_with_name(name))

    def has_success_message(self):
        return self.find_message_and_dismiss(messages.SUCCESS)

    def has_error_message(self):
        return self.find_message_and_dismiss(messages.ERROR)
