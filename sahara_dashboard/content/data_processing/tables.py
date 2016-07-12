# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from horizon import tables

import sahara_dashboard.api.sahara as saharaclient


class SaharaPaginateTabbedTable(tables.DataTable):
    def get_pagination_string(self):
        return "tab=%s&limit=%s&marker=%s" % (
            self.tab_name,
            saharaclient.get_page_size(self.request),
            self.data.next
        )

    def get_prev_pagination_string(self):
        if self.data.prev is None:
            return "tab=%s&limit=%s" % (
                self.tab_name,
                saharaclient.get_page_size(self.request)
            )
        return "tab=%s&limit=%s&marker=%s" % (
            self.tab_name,
            saharaclient.get_page_size(self.request),
            self.data.prev
        )

    def has_more_data(self):
        return hasattr(self.data, 'next') and self.data.next is not None

    def has_prev_data(self):
        if hasattr(self.data, 'prev'):
            if 'tab' in self.request.GET:
                if self.tab_name == self.request.GET['tab']:
                    if 'marker' not in self.request.GET:
                        return False
                    else:
                        return True
        return False
