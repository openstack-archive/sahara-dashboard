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

from horizon import exceptions
from horizon import tabs
from horizon.tabs import base

from sahara_dashboard import utils as u


class SaharaTableTab(tabs.TableTab):
    def get_server_filter_info(self, request, table):
        filter_action = table._meta._filter_action
        if filter_action is None or filter_action.filter_type != 'server':
            return None
        param_name = filter_action.get_param_name()
        filter_string = request.POST.get(param_name)
        filter_string_session = request.session.get(param_name, "")
        changed = (filter_string is not None
                   and filter_string != filter_string_session)
        if filter_string is None:
            filter_string = filter_string_session
        filter_field_param = param_name + '_field'
        filter_field = request.POST.get(filter_field_param)
        filter_field_session = request.session.get(filter_field_param)
        if filter_field is None and filter_field_session is not None:
            filter_field = filter_field_session
        setattr(table.base_actions["filter"], "filter_string", filter_string)
        setattr(table.base_actions["filter"], "filter_field", filter_field)
        filter_info = {
            'action': filter_action,
            'value_param': param_name,
            'value': filter_string,
            'field_param': filter_field_param,
            'field': filter_field,
            'changed': changed
        }
        return filter_info


class PaginationFriendlyTabGroup(tabs.TabGroup):
    def load_tab_data(self):
        """Preload all data that for the tabs that will be displayed."""
        request_without_marker = u.delete_pagination_params_from_request(
            self.request, save_limit=True)
        for tab in self._tabs.values():
            current_tab_id = tab.slug

            tab_request = self.request.GET.get('tab')
            request_tab_id = None

            if tab_request:
                request_tab_id = tab_request.split(base.SEPARATOR)[1]
            if request_tab_id and current_tab_id != request_tab_id:
                try:
                    tab.request = request_without_marker
                    tab._data = tab.get_context_data(request_without_marker)
                except Exception:
                    tab._data = False
                    exceptions.handle(request_without_marker)

            if tab.load and not tab.data_loaded:
                try:
                    tab._data = tab.get_context_data(self.request)
                except Exception:
                    tab._data = False
                    exceptions.handle(self.request)
