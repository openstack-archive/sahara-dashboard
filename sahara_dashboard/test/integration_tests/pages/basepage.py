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
from openstack_dashboard.test.integration_tests.regions import messages
from openstack_dashboard.test.integration_tests.regions import tables


class BaseDataProcessingPage(basepage.BaseNavigationPage):

    TABLE_NAME = ""

    # index of name column in binary jobs table
    TABLE_NAME_COLUMN = 'name'

    def __new__(cls, *args, **kwargs):
        table_bases = (tables.TableRegion,) + cls.get_table_mixins()
        cls.TableRegion = type('PageTableRegion', table_bases,
                               {'name': cls.TABLE_NAME})
        return super(BaseDataProcessingPage, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def get_table_mixins(cls):
        return ()

    def _get_row_with_name(self, name, name_column=TABLE_NAME_COLUMN):
        try:
            return self.table.get_row(name_column, name)
        except Exception:
            return None

    @property
    def table(self):
        return self.TableRegion(self.driver, self.conf)

    def is_present(self, name):
        return bool(self._get_row_with_name(name))

    def has_success_message(self):
        return self.find_message_and_dismiss(messages.SUCCESS)

    def has_error_message(self):
        return self.find_message_and_dismiss(messages.ERROR)
