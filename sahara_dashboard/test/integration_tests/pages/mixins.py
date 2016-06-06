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
from openstack_dashboard.test.integration_tests.regions import tables


class TableCreateWithPluginMixin(object):

    PLUGIN_CHOOSE_FORM_FIELDS = (
        'vanilla_version',
        'cdh_version',
        'plugin_name',
        'spark_version',
        'fake_version',
        'storm_version',
        'mapr_version'
    )

    @tables.bind_table_action('create')
    def get_create_form(self, button):
        button.click()
        return forms.FormRegion(self.driver, self.conf,
                                field_mappings=self.PLUGIN_CHOOSE_FORM_FIELDS)


class PluginSelectMixin(object):

    @classmethod
    def get_table_mixins(cls):
        return (super(PluginSelectMixin, cls).get_table_mixins() +
                (TableCreateWithPluginMixin,))

    def choose_plugin(self, plugin_name, plugin_version):
        form = self.table.get_create_form()
        form.plugin_name.text = plugin_name
        for f_name, field in form.fields.items():
            if not f_name.endswith('version'):
                continue
            if field.is_displayed():
                field.text = plugin_version
                break
        else:
            raise Exception("Can't find element to set version")
        form.submit()


class TableDeleteMixin(object):
    @tables.bind_table_action('delete')
    def get_delete_form(self, button):
        button.click()
        return forms.BaseFormRegion(self.driver, self.conf)


class DeleteMixin(object):

    @classmethod
    def get_table_mixins(cls):
        return (super(DeleteMixin, cls).get_table_mixins() +
                (TableDeleteMixin,))

    def delete_many(self, names=()):
        for name in names:
            row = self._get_row_with_name(name)
            if row is not None:
                row.mark()
        self.table.get_delete_form().submit()

    def delete(self, name):
        return self.delete_many([name])
