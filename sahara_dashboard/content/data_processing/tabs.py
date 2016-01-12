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

from horizon import tabs


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
