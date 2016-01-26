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


class TabbedFormRegion(forms.TabbedFormRegion):

    def __init__(self, driver, conf, field_mappings=None, default_tab=0):
        self.original_field_mappings = field_mappings
        super(TabbedFormRegion, self).__init__(driver, conf,
                                               field_mappings=field_mappings)

    def _set_checkbox_group(self, group_name, values=()):
        for el in self.src_elem.find_elements_by_xpath(
            './/input[@name="{}"]'.format(group_name)
        ):
            elem_id = el.get_attribute('id')
            label = self.src_elem.find_element_by_css_selector(
                'label[for={}]'.format(elem_id))
            if (label.text in values) != el.is_selected():
                label.click()

    def set_values(self, **kwargs):
        for tab_num, fields in enumerate(self.original_field_mappings):
            self.switch_to(tab_num)
            for key in fields:
                value = kwargs.get(key)
                if value is None:
                    continue
                if isinstance(value, (list, tuple)):
                    self._set_checkbox_group(key, value)
                    continue
                field = getattr(self, key)
                if hasattr(field, 'mark'):
                    if value:
                        field.mark()
                    else:
                        field.unmark()
                else:
                    field.text = value
