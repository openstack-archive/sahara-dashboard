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


class JobBinariesTable(tables.TableRegion):
    name = 'job_binaries'
    CREATE_BINARY_FORM_FIELDS = {
        "name": "job_binary_name",
        "type": "job_binary_type",
        "url": "job_binary_url",
        "internal": "job_binary_internal",
        "file": "job_binary_file",
        "script_name": "job_binary_script_name",
        "script": "job_binary_script",
        "username": "job_binary_username",
        "password": "job_binary_password",
        "description": "job_binary_description"
    }

    @tables.bind_table_action('create')
    def create_job(self, create_button):
        create_button.click()
        return forms.FormRegion(
            self.driver, self.conf,
            field_mappings=self.CREATE_BINARY_FORM_FIELDS)

    @tables.bind_table_action('delete')
    def delete_job(self, delete_button):
        delete_button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class JobbinariesPage(basepage.BaseNavigationPage):

    JOB_BINARIES_TABLE_NAME_COLUMN = 'name'

    def __init__(self, driver, conf):
        super(JobbinariesPage, self).__init__(driver, conf)
        self._page_title = "Data Processing"

    def _get_row_with_job_binary_name(self, name):
        return self.job_binaries_table.get_row(
            self.JOB_BINARIES_TABLE_NAME_COLUMN, name)

    @property
    def job_binaries_table(self):
        return JobBinariesTable(self.driver, self.conf)

    def delete_job_binary(self, name):
        row = self._get_row_with_job_binary_name(name)
        row.mark()
        confirm_delete_form = self.job_binaries_table.delete_job()
        confirm_delete_form.submit()

    def create_job_binary(self, binary_name, script_name):
        create_job_binary_form = self.job_binaries_table.create_job()

        create_job_binary_form.name.text = binary_name
        create_job_binary_form.type.text = "Internal database"
        create_job_binary_form.internal.text = "*Create a script"
        create_job_binary_form.script_name.text = script_name
        create_job_binary_form.script.text = "test_script_text"
        create_job_binary_form.description.text = "test description"
        create_job_binary_form.submit()

    def is_job_binary_present(self, name):
        return bool(self._get_row_with_job_binary_name(name))
