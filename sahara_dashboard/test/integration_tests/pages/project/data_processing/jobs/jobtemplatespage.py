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
from selenium.webdriver.common import by

from sahara_dashboard.test.integration_tests.pages import basepage
from sahara_dashboard.test.integration_tests.pages import mixins


class CreateMixin(object):
    CREATE_FIELD_MAPPING = (
        ('job_name', 'job_type', 'main_binary', 'job_description'),
        ('lib_binaries',),
    )

    LAUNCH_ON_EXIST_CLUSTER_FIELD_MAPPING = (
        ('job_input', 'job_output', 'cluster'),
        ('adapt_spark_swift', 'datasource_substitute', 'streaming_mapper',
            'streaming_reducer'),
        (),
    )

    @tables.bind_table_action('create job')
    def get_create_form(self, button):
        button.click()
        return forms.TabbedFormRegion(self.driver, self.conf,
                                      field_mappings=self.CREATE_FIELD_MAPPING)

    @tables.bind_row_action('launch-job-existing')
    def get_launch_on_exists_form(self, button, row):
        button.click()
        return forms.TabbedFormRegion(
            self.driver, self.conf,
            field_mappings=self.LAUNCH_ON_EXIST_CLUSTER_FIELD_MAPPING)


class JobtemplatesPage(mixins.DeleteMixin, basepage.BaseDataProcessingPage):

    TABLE_NAME = "job_templates"

    @classmethod
    def get_table_mixins(cls):
        return super(JobtemplatesPage, cls).get_table_mixins() + (CreateMixin,)

    def create(self, name, job_type, binary_name, libs=()):
        form = self.table.get_create_form()
        form.job_name.text = name
        form.job_type.text = job_type
        if binary_name is not None:
            form.main_binary.text = binary_name
        form.switch_to(1)
        for lib in libs:
            form.lib_binaries.text = lib
            form.src_elem.find_element_by_id("add_lib_button").click()
        form.submit()

    def launch_on_exists(self, job_name, input_name, output_name,
                         cluster_name, adapt_swift=True,
                         datasource_substitution=True, configuration=None,
                         parameters=None, arguments=(),
                         mapper=None, reducer=None):
        configuration = configuration or {}
        parameters = parameters or {}
        row = self._get_row_with_name(job_name)
        form = self.table.get_launch_on_exists_form(row)
        if input_name is not None:
            form.job_input.text = input_name
        if output_name is not None:
            form.job_output.text = output_name
        form.cluster.text = cluster_name

        form.switch_to(1)
        if adapt_swift:
            form.adapt_spark_swift.mark()
        else:
            form.adapt_spark_swift.unmark()
        if datasource_substitution:
            form.datasource_substitute.mark()
        else:
            form.datasource_substitute.unmark()

        if mapper is not None:
            form.streaming_mapper.text = mapper
        if reducer is not None:
            form.streaming_reducer.text = reducer

        locator = (by.By.ID, 'configs')
        if form._is_element_visible(*locator):
            config_block = form.src_elem.find_element(*locator)
            add_btn = config_block.find_element_by_link_text('Add')
            for key, value in configuration.items():
                add_btn.click()
                inputs = config_block.find_elements_by_css_selector(
                    'input[type=text]')[-2:]
                inputs[0].send_keys(key)
                inputs[1].send_keys(value)

        locator = (by.By.ID, 'params')
        if form._is_element_visible(*locator):
            params_block = form.src_elem.find_element(*locator)
            add_btn = params_block.find_element_by_link_text('Add')
            for key, value in parameters.items():
                add_btn.click()
                inputs = params_block.find_elements_by_css_selector(
                    'input[type=text]')[-2:]
                inputs[0].send_keys(key)
                inputs[1].send_keys(value)

        locator = (by.By.ID, 'args_array')
        if form._is_element_visible(*locator):
            args_block = form.src_elem.find_element(*locator)
            add_btn = args_block.find_element_by_link_text('Add')
            for value in arguments:
                add_btn.click()
                input_el = args_block.find_elements_by_css_selector(
                    'input[type=text]')[-1]
                input_el.send_keys(value)
        form.submit()
