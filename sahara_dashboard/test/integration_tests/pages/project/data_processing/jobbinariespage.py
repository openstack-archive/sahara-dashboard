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

from selenium.webdriver.common import by

from openstack_dashboard.test.integration_tests.pages import basepage
from openstack_dashboard.test.integration_tests.regions import forms
from openstack_dashboard.test.integration_tests.regions import tables


class JobbinariesPage(basepage.BaseNavigationPage):

    _job_binaries_table_locator = (by.By.CSS_SELECTOR, 'table#job_binaries')
    _create_job_binary_form_locator = (by.By.CSS_SELECTOR, 'div.modal-dialog')
    _confirm_job_binary_deletion_form =\
        (by.By.CSS_SELECTOR, 'div.modal-dialog')

    JOB_BINARIES_TABLE_NAME = "job_binaries"
    JOB_BINARIES_TABLE_ACTIONS = ("create", "delete")
    JOB_BINARIES_ROW_ACTIONS = {
        tables.ComplexActionRowRegion.PRIMARY_ACTION: "delete_job_binary",
        tables.ComplexActionRowRegion.SECONDARY_ACTIONS:
            ("download_job_binary",)
    }

    BINARY_NAME = "job_binary_name"
    BINARY_STORAGE_TYPE = "job_binary_type"
    BINARY_URL = "job_binary_url"
    INTERNAL_BINARY = "job_binary_internal"
    BINARY_PATH = "job_binary_file"
    SCRIPT_NAME = "job_binary_script_name"
    SCRIPT_TEXT = "job_binary_script"
    USERNAME = "job_binary_username"
    PASSWORD = "job_binary_password"
    DESCRIPTION = "job_binary_description"

    CREATE_BINARY_FORM_FIELDS = (
        BINARY_NAME,
        BINARY_STORAGE_TYPE,
        BINARY_URL,
        INTERNAL_BINARY,
        BINARY_PATH,
        SCRIPT_NAME,
        SCRIPT_TEXT,
        USERNAME,
        PASSWORD,
        DESCRIPTION
    )

    # index of name column in binary jobs table
    JOB_BINARIES_TABLE_NAME_COLUMN = 0

    # fields that are set via text setter
    _TEXT_FIELDS = (BINARY_NAME, BINARY_STORAGE_TYPE, INTERNAL_BINARY)

    def __init__(self, driver, conf):
        super(JobbinariesPage, self).__init__(driver, conf)
        self._page_title = "Data Processing"

    def _get_row_with_job_binary_name(self, name):
        return self.job_binaries_table.get_row(
            self.JOB_BINARIES_TABLE_NAME_COLUMN, name)

    @property
    def job_binaries_table(self):
        src_elem = self._get_element(*self._job_binaries_table_locator)
        return tables.ComplexActionTableRegion(self.driver,
                                               self.conf, src_elem,
                                               self.JOB_BINARIES_TABLE_NAME,
                                               self.JOB_BINARIES_TABLE_ACTIONS,
                                               self.JOB_BINARIES_ROW_ACTIONS)

    @property
    def create_job_binary_form(self):
        src_elem = self._get_element(*self._create_job_binary_form_locator)
        return forms.FormRegion(self.driver, self.conf, src_elem,
                                self.CREATE_BINARY_FORM_FIELDS)

    @property
    def confirm_delete_job_binaries_form(self):
        src_elem = self._get_element(*self._confirm_job_binary_deletion_form)
        return forms.BaseFormRegion(self.driver, self.conf, src_elem)

    def delete_job_binary(self, name):
        row = self._get_row_with_job_binary_name(name)
        row.mark()
        self.job_binaries_table.delete.click()
        self.confirm_delete_job_binaries_form.submit.click()
        self.wait_till_popups_disappear()

    def create_job_binary(self, job_data):
        self.job_binaries_table.create.click()

        self.create_job_binary_form.set_field_values(job_data)
        self.create_job_binary_form.submit.click()
        self.wait_till_popups_disappear()

    def is_job_binary_present(self, name):
        return bool(self._get_row_with_job_binary_name(name))
