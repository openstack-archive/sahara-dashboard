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

from sahara_dashboard.test.integration_tests.pages import basepage
from sahara_dashboard.test.integration_tests.pages import mixins


class JobsPage(mixins.DeleteMixin, basepage.BaseDataProcessingPage):

    TABLE_NAME = "jobs"

    def _get_row_by_template_name(self, name):
        return self.table.get_row('job_name', name)

    def is_job_succeeded(self, name):
        row = self._get_row_by_template_name(name)
        status = row.cells['status'].text
        if status.startswith('Error'):
            raise Exception('Job {} status is {}'.format(name, status))
        return status == "Succeeded"

    def delete_many(self, names=()):
        for name in names:
            row = self._get_row_by_template_name(name)
            if row is not None:
                row.mark()
        self.table.get_delete_form().submit()

    def delete(self, name):
        self.delete_many([name])

    def wait_until_job_succeeded(self, name, timeout=None):
        self._wait_until(lambda x: self.is_job_succeeded(name),
                         timeout=timeout)

    def get_details(self, template_name):
        row = self._get_row_by_template_name(template_name)
        row.cells['name'].find_element_by_tag_name('a').click()
        details = {}
        self.driver.implicitly_wait(0)
        items = self.driver.find_elements_by_css_selector('div.detail dt')
        for item in items:
            key = item.text
            value_elem = item.find_element_by_xpath('./following-sibling::*')
            if value_elem.tag_name != "dd":
                continue
            sub_elements = value_elem.find_elements_by_css_selector(
                'li > span')
            if sub_elements:
                value = {}
                for sub_element in sub_elements:
                    sub_key = sub_element.text.strip(':')
                    value[sub_key] = set()
                    for elem in sub_element.find_elements_by_xpath(
                        './following-sibling::ul/li'
                    ):
                        value[sub_key].add(elem.text)
            else:
                value = value_elem.text
            details[key] = value
        self.driver.implicitly_wait(30)
        return details
