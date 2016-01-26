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

from sahara_dashboard.test.integration_tests.pages import basepage
from sahara_dashboard.test.integration_tests.pages import mixins


class NodegrouptemplatesPage(mixins.PluginSelectMixin, mixins.DeleteMixin,
                             basepage.BaseDataProcessingPage):

    TABLE_NAME = "nodegroup_templates"

    CREATE_FIELD_MAPPING = (
        ('flavor', 'nodegroup_name', 'availability_zone', 'floating_ip_pool',
            'proxygateway'),
        (),
        (),
    )

    @property
    def create_form(self):
        return forms.TabbedFormRegion(
            self.driver, self.conf, field_mappings=self.CREATE_FIELD_MAPPING)

    def create(self, plugin_name, plugin_version, name, flavor,
               floating_ip_pool=None, availability_zone='nova',
               proxygateway=False, processes=()):
        self.choose_plugin(plugin_name, plugin_version)
        form = self.create_form
        form.nodegroup_name.text = name
        form.flavor.text = flavor
        form.availability_zone.text = availability_zone
        if floating_ip_pool is not None:
            form.floating_ip_pool.text = floating_ip_pool
        if proxygateway:
            form.proxygateway.mark()
        form.switch_to(1)
        for el in form.src_elem.find_elements_by_xpath(
            './/input[@name="processes"]'
        ):
            if el.get_attribute('value') in processes:
                el.click()
        form.submit()
