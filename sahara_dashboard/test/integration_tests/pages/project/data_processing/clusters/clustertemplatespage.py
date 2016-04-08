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


class ClusterTemplateForm(forms.TabbedFormRegion):
    CREATE_FIELD_MAPPING = (
        ('cluster_template_name', 'description', 'use_autoconfig',
            'anti_affinity'),
        (),
        ('CONF:general:Timeout for disk preparing',
            'CONF:general:Enable NTP service',
            'CONF:general:URL of NTP server',
            'CONF:general:Heat Wait Condition timeout',
            'CONF:general:Enable XFS')
    )

    def __init__(self, *args, **kwargs):
        kwargs['field_mappings'] = self.CREATE_FIELD_MAPPING
        super(ClusterTemplateForm, self).__init__(*args, **kwargs)

    def set_nodegroup_templates(self, node_group_templates):
        self.switch_to(1)
        template_el = self.src_elem.find_element_by_name('template')
        add_button = self.src_elem.find_element_by_id('add_group_button')
        to_add_templates = list(node_group_templates)
        groups_table = self.src_elem.find_element_by_id('groups_table')
        if groups_table.is_displayed():
            for row in groups_table.find_elements_by_css_selector(
                'tr.data-template-row'
            ):
                name = row.find_element_by_xpath('.//input[1]').get_attribute(
                    'value')
                if name in to_add_templates:
                    to_add_templates.remove(name)
                else:
                    row.find_element_by_css_selector(
                        'input[type=button]').click()

        for template_name in to_add_templates:
            for option in template_el.find_elements_by_tag_name('option'):
                if option.text == template_name:
                    option.click()
                    add_button.click()
                    break


class UpdateMixin(object):
    @tables.bind_row_action('edit')
    def get_edit_form(self, button, row):
        button.click()
        return ClusterTemplateForm(self.driver, self.conf)


class ClustertemplatesPage(mixins.PluginSelectMixin, mixins.DeleteMixin,
                           basepage.BaseDataProcessingPage):

    TABLE_NAME = "cluster_templates"

    @classmethod
    def get_table_mixins(cls):
        return (super(ClustertemplatesPage, cls).get_table_mixins() +
                (UpdateMixin,))

    @property
    def create_form(self):
        return ClusterTemplateForm(self.driver, self.conf)

    def create(self, plugin_name, plugin_version, name, node_group_templates,
               **kwargs):
        self.choose_plugin(plugin_name, plugin_version)
        form = self.create_form
        kwargs.update({
            'cluster_template_name': name
        })
        form.set_values(**kwargs)
        form.set_nodegroup_templates(node_group_templates)
        form.submit()

    def update(self, name, node_group_templates=(), **kwargs):
        row = self._get_row_with_name(name)
        form = self.table.get_edit_form(row)
        form.set_values(**kwargs)
        form.set_nodegroup_templates(node_group_templates)
        form.submit()

    def get_details(self, name):
        details = {'node_groups': {}}
        row = self._get_row_with_name(name)
        for node_group in row.cells['node_groups'].text.split('\n'):
            key, delimiter, value = node_group.partition(':')
            if delimiter == ':':
                details['node_groups'][key] = value.strip()
        self.table.src_elem.find_element_by_link_text(name).click()
        items = self.driver.find_elements_by_css_selector('div.detail dt')
        for item in items:
            key = item.text
            value_elem = item.find_element_by_xpath('./following-sibling::*')
            if value_elem.tag_name != "dd":
                continue
            value = value_elem.text
            details[key] = value
        self.driver.find_element_by_link_text('Configuration Details').click()
        items = self.driver.find_elements_by_css_selector('div.detail > dl li')
        for item in items:
            key, delimiter, value = item.text.partition(':')
            if delimiter == ':':
                details[key] = value.strip()
        for key, value in details.items():
            if '\n' in value:
                details[key] = set(value.split('\n'))
        return details

    def get_nodegroup_details(self, cluster_tpl_name, node_group_name):
        self.table.src_elem.find_element_by_link_text(cluster_tpl_name).click()
        self.driver.find_element_by_link_text('Node Groups').click()
        details = {}
        groups = self.driver.find_elements_by_css_selector(
            'div.tab-pane.active dl')
        for group in groups:
            if node_group_name not in group.text:
                continue
            for item in group.find_elements_by_tag_name('dt'):
                key = item.text
                value_elem = item.find_element_by_xpath(
                    './following-sibling::*')
                if value_elem.tag_name != "dd":
                    continue
                value = value_elem.text
                details[key] = value
        for key, value in details.items():
            if '\n' in value:
                details[key] = set(value.split('\n'))
        return details
