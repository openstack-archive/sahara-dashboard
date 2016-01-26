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

from openstack_dashboard.test.integration_tests.regions import tables

from sahara_dashboard.test.integration_tests.pages import basepage
from sahara_dashboard.test.integration_tests.pages import mixins
from sahara_dashboard.test.integration_tests.regions import forms


CREATE_FIELD_MAPPING = (
    ('nodegroup_name', 'description', 'flavor', 'availability_zone', 'storage',
        'volumes_per_node', 'volumes_size', 'volume_type',
        'volume_local_to_instance', 'volumes_availability_zone',
        'floating_ip_pool', 'use_autoconfig', 'proxygateway'),
    ('processes',),
    ('security_autogroup', 'security_groups'),
)


class UpdateMixin(object):
    @tables.bind_row_action('edit')
    def get_edit_form(self, button, row):
        button.click()
        return forms.TabbedFormRegion(
            self.driver, self.conf,
            field_mappings=CREATE_FIELD_MAPPING)


class NodegrouptemplatesPage(mixins.PluginSelectMixin, mixins.DeleteMixin,
                             basepage.BaseDataProcessingPage):

    TABLE_NAME = "nodegroup_templates"

    @classmethod
    def get_table_mixins(cls):
        return (super(NodegrouptemplatesPage, cls).get_table_mixins() +
                (UpdateMixin,))

    @property
    def create_form(self):
        return forms.TabbedFormRegion(
            self.driver, self.conf, field_mappings=CREATE_FIELD_MAPPING)

    def create(self, plugin_name, plugin_version, nodegroup_name, flavor,
               floating_ip_pool=None, availability_zone='nova',
               proxygateway=False, processes=(), **kwargs):
        self.choose_plugin(plugin_name, plugin_version)
        form = self.create_form
        kwargs.update({
            'nodegroup_name': nodegroup_name,
            'flavor': flavor,
            'floating_ip_pool': floating_ip_pool,
            'availability_zone': availability_zone,
            'proxygateway': proxygateway,
            'processes': processes,
        })
        form.set_values(**kwargs)
        form.submit()

    def update(self, group_name, **kwargs):
        row = self._get_row_with_name(group_name)
        form = self.table.get_edit_form(row)
        form.set_values(**kwargs)
        form.submit()

    def get_details(self, name):
        self.table.src_elem.find_element_by_link_text(name).click()
        items = self.driver.find_elements_by_css_selector('div.detail > dl')
        self._turn_off_implicit_wait()
        details = {}
        for item in items:
            names = [x.text for x in item.find_elements_by_tag_name('dt')]
            values = [x.text for x in item.find_elements_by_tag_name('dd')]
            details.update(zip(names, values))
        self._turn_on_implicit_wait()
        return details
