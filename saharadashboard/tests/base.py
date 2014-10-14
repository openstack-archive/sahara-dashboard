# Copyright (c) 2013 Mirantis Inc.
#
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

import logging
import os
import time
import traceback

import selenium.common.exceptions as selenim_except
from selenium import webdriver
import selenium.webdriver.common.by as by
from swiftclient import client as swift_client
import unittest2

import saharadashboard.tests.configs.config as cfg


logger = logging.getLogger('swiftclient')
logger.setLevel(logging.WARNING)


class UITestCase(unittest2.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.ifFail = False
            cls.driver = webdriver.Firefox()
            cls.driver.get(cfg.common.base_url + "/")
            cls.find_clear_send(by.By.ID, "id_username", cfg.common.user)
            cls.find_clear_send(by.By.ID, "id_password", cfg.common.password)
            cls.driver.find_element_by_xpath(
                "//button[@type='submit']").click()
        except Exception:
            traceback.print_exc()
            cls.ifFail = True
            pass

    def setUp(self):
        if self.ifFail:
            self.fail("setUpClass method is fail")
        self.await_element(by.By.CLASS_NAME, 'clearfix',
                           'authorization failed')

    def image_registry(self, image_name, user_name=None, description=None,
                       tags_to_add=None, tags_to_remove=None, positive=True,
                       close_window=True, message=''):
        if positive:
            message = 'Success: Successfully updated image.'
        self.image_registry_helper(image_name, user_name, description,
                                   tags_to_add, tags_to_remove, positive,
                                   close_window, message, 'Registry')

    def edit_tags_by_image_name(self, image_name, user_name=None,
                                description=None, tags_to_add=None,
                                positive=True, message=None, close_window=True,
                                tags_to_remove=None):
        if positive:
            message = 'Success: Successfully updated image.'
        self.image_registry_helper(image_name, user_name, description,
                                   tags_to_add, tags_to_remove, positive,
                                   close_window, message, 'Edit')

    def create_node_group_template(
            self, name, list_processes, plugin, flavor=None, params=None,
            storage={'type': 'Ephemeral Drive'}, description=None,
            positive=True, message=None, close_window=True):
        driver = self.driver
        if not flavor:
            flavor = cfg.common.flavor
        driver.get(cfg.common.base_url +
                   "/project/data_processing/nodegroup_templates/")
        self.await_element(by.By.ID, "nodegroup_templates__action_create")
        driver.find_element_by_id("nodegroup_templates__action_create").click()
        self.choose_plugin_name(plugin.plugin_name, plugin.hadoop_version,
                                name, description, "id_nodegroup_name")
        self.driver.find_element_by_xpath(
            "//select[@id='id_flavor']/option[text()='%s']" % flavor).click()
        self.driver.find_element_by_xpath(
            "//*[@id='id_storage']/option[text()='%s']"
            % storage['type']).click()
        if storage['type'] == "Cinder Volume":
            self.find_clear_send(by.By.ID, "id_volumes_per_node",
                                 storage['volume_per_node'])
            self.find_clear_send(by.By.ID, "id_volumes_size",
                                 storage['volume_size'])
        if cfg.common.floationg_ip_pool:
            self.driver.find_element_by_xpath(
                "//*[@id='id_floating_ip_pool']/option[text()='%s']"
                % cfg.common.floationg_ip_pool).click()
        if cfg.common.auto_security_groups != driver.find_element_by_id(
                "id_autogroup").is_selected():
            driver.find_element_by_id("id_autogroup").click()
        if cfg.common.security_groups:
            # create dictionary with existing security groups
            actual_groups = {}
            for sec_group in driver.find_elements_by_xpath(
                    "//label[contains(@for, 'id_groups_')]"):
                actual_groups[sec_group.text] = sec_group
            # search specified in config file security groups of existing
            for sec_group in cfg.common.security_groups:
                if sec_group not in actual_groups:
                    self.fail("Security group with name %s not "
                              "found. Aborting." % sec_group)
                if not actual_groups[sec_group].is_selected():
                    actual_groups[sec_group].click()
        processes = []
        for process in list_processes:
            number_pr = self.search_id_processes(process, plugin)
            driver.find_element_by_id(
                "id_processes_%s" % str(number_pr)).click()
            processes.append(driver.find_element_by_id(
                "id_processes_%s" % str(number_pr)).
                find_element_by_xpath('..').text)
        if params:
            self.config_helper(params)
        self.click_visible_key("//input[@value='Create']")
        if not message:
            message = "Success: Created Node Group Template %s" % name
        if close_window:
            self.check_create_object(
                name, positive, message,
                [{2: [name]},
                 {3: [plugin.plugin_overview_name]},
                 {4: [plugin.hadoop_version]}, {5: processes}])
        else:
            self.error_helper(message)

    def create_cluster_template(
            self, name, node_groups, plugin, description=None,
            close_window=True, anti_affinity_groups=None, positive=True,
            message=None, params=None):
        driver = self.driver
        driver.get(cfg.common.base_url +
                   "/project/data_processing/cluster_templates/")
        self.await_element(by.By.ID, "cluster_templates__action_create")
        driver.find_element_by_id("cluster_templates__action_create").click()
        self.choose_plugin_name(plugin.plugin_name, plugin.hadoop_version,
                                name, description, "id_cluster_template_name")
        if anti_affinity_groups:
            for group in anti_affinity_groups:
                driver.find_element_by_id(
                    "id_anti_affinity_%s" % self.search_id_processes(
                        group, plugin)).click()
        driver.find_element_by_link_text("Node Groups").click()
        number_to_add = 0
        node_groups_list = []
        for node_group, count in node_groups.items():
            driver.find_element_by_xpath(
                "//select[@id='template_id']/option[text()='%s']"
                % node_group).click()
            driver.find_element_by_id("add_group_button").click()
            self.find_clear_send(by.By.ID, "count_%d" % number_to_add, count)
            node_groups_list.append("%s: %d" % (node_group, count))
            number_to_add += 1
        if params:
            self.config_helper(params)
        self.click_visible_key("//input[@value='Create']")
        if not message:
            message = "Success: Created Cluster Template %s" % name
        if close_window:
            self.check_create_object(
                name, positive, message,
                [{2: [name]},
                 {3: [plugin.plugin_overview_name]},
                 {4: [plugin.hadoop_version]}, {5: node_groups_list},
                 {6: [description if description else '']}])
        else:
            self.error_helper(message)

    def create_cluster(self, name, cluster_template, plugin, keypair=None,
                       close_window=True, description=None, positive=True,
                       await_run=True, message=None):
        driver = self.driver
        driver.get(cfg.common.base_url + "/project/data_processing/clusters/")
        self.await_element(by.By.ID, "clusters__action_create")
        driver.find_element_by_id("clusters__action_create").click()
        self.choose_plugin_name(plugin.plugin_name, plugin.hadoop_version,
                                name, description, "id_cluster_name")
        driver.find_element_by_xpath("//select[@id='id_cluster_template']/"
                                     "option[text()='%s']" %
                                     cluster_template).click()
        driver.find_element_by_xpath("//select[@id='id_image']/option"
                                     "[text()='%s']" %
                                     plugin.base_image).click()
        if not keypair:
            keypair = cfg.common.keypair
        driver.find_element_by_xpath("//select[@id='id_keypair']"
                                     "/option[text()='%s']" % keypair).click()
        if cfg.common.neutron_management_network:
            driver.find_element_by_xpath(
                "//select[@id='id_neutron_management_network']/option[text()="
                "'%s']" % cfg.common.neutron_management_network).click()
        self.click_visible_key("//input[@value='Create']")
        if not message:
            message = 'Success: Created Cluster %s' % name
        if close_window:
            self.check_create_object(name, positive, message)
        else:
            self.error_helper(message)
        if await_run:
            self.await_cluster_active(name)

    def create_data_source(self, name, url, close_window=True,
                           description=None, positive=True, message=None):

        driver = self.driver
        driver.get(cfg.common.base_url +
                   "/project/data_processing/data_sources/")
        self.await_element(by.By.ID, "data_sources__action_create data source")
        driver.find_element_by_id(
            "data_sources__action_create data source").click()

        self.await_element(by.By.ID, "id_data_source_name")

        self.find_clear_send(by.By.ID, "id_data_source_name", name)
        self.find_clear_send(by.By.ID, "id_data_source_url", url)
        self.find_clear_send(by.By.ID, "id_data_source_credential_user",
                             cfg.common.user)
        self.find_clear_send(by.By.ID, "id_data_source_credential_pass",
                             cfg.common.password)
        if description:
            self.find_clear_send(by.By.ID, "id_data_source_description",
                                 description)

        driver.find_element_by_xpath("//input[@value='Create']").click()

        if not message:
            message = 'Success: Data source created'
        if close_window:
            self.check_create_object(name, positive, message)
        else:
            self.error_helper(message)

    def create_job_binary(self, name, parameters_of_storage, description=None,
                          positive=True, message=None, close_window=True):

        driver = self.driver
        storage_type = parameters_of_storage['storage_type']
        driver.get(cfg.common.base_url +
                   "/project/data_processing/job_binaries/")
        self.await_element(by.By.ID, "job_binaries__action_create job binary")
        driver.find_element_by_id(
            "job_binaries__action_create job binary").click()

        self.await_element(by.By.ID, "id_job_binary_name")

        self.find_clear_send(by.By.ID, "id_job_binary_name", name)
        driver.find_element_by_xpath("//select[@id='id_job_binary_type']/optio"
                                     "n[text()='%s']" % storage_type).click()

        if storage_type == 'Swift':
            self.find_clear_send(by.By.ID, "id_job_binary_url",
                                 parameters_of_storage['url'])
            self.find_clear_send(by.By.ID, "id_job_binary_username",
                                 cfg.common.user)
            self.find_clear_send(by.By.ID, "id_job_binary_password",
                                 cfg.common.password)

        elif storage_type == 'Internal database':
            internal_binary = parameters_of_storage['Internal binary']
            driver.find_element_by_xpath(
                "//select[@id='id_job_binary_internal']/option[text()"
                "='%s']" % internal_binary).click()
            if internal_binary == '*Upload a new file':
                file = '%s/saharadashboard/tests/resources/%s' % (
                    os.getcwd(), parameters_of_storage['filename'])
                driver.find_element_by_id('id_job_binary_file').send_keys(file)

            elif internal_binary == '*Create a script':
                self.find_clear_send(by.By.ID, "id_job_binary_script_name",
                                     parameters_of_storage['script_name'])
                self.find_clear_send(by.By.ID, "id_job_binary_script",
                                     parameters_of_storage['script_text'])

        if description:
            self.find_clear_send(by.By.ID, "id_job_binary_description",
                                 description)

        driver.find_element_by_xpath("//input[@value='Create']").click()

        if not message:
            message = 'Success: Successfully created job binary'
        if close_window:
            self.check_create_object(name, positive, message)
        else:
            self.error_helper(message)

    def create_job(self, name, job_type, main=None, libs=None,
                   close_window=True, description=None, positive=True,
                   message=None):

        driver = self.driver
        driver.get(cfg.common.base_url + "/project/data_processing/jobs/")
        self.await_element(by.By.ID, "jobs__action_create job")
        driver.find_element_by_id("jobs__action_create job").click()

        self.await_element(by.By.ID, "id_job_name")
        self.find_clear_send(by.By.ID, "id_job_name", name)
        driver.find_element_by_xpath(
            "//select[@id='id_job_type']/option[text()='%s']"
            % job_type).click()
        if main:
            driver.find_element_by_xpath(
                "//select[@id='id_main_binary']/option[text()='%s']"
                % main).click()
        if description:
            self.find_clear_send(by.By.ID, "id_job_description", description)
        if libs:
            driver.find_element_by_link_text('Libs').click()
            self.await_element(by.By.ID, "id_lib_binaries")
            for lib in libs:
                driver.find_element_by_xpath(
                    "//select[@id='id_lib_binaries']/option[text()='%s']"
                    % lib).click()
                driver.find_element_by_id('add_lib_button').click()

        driver.find_element_by_xpath("//input[@value='Create']").click()

        if not message:
            message = 'Success: Job created'
        if close_window:
            self.check_create_object(name, positive, message)
        else:
            self.error_helper(message)

    def launch_job_on_existing_cluster(self, name, input, output, cluster,
                                       configure=None, positive=True,
                                       message=None, close_window=True,
                                       await_launch=True):

        driver = self.driver
        driver.get(cfg.common.base_url + "/project/data_processing/jobs/")
        self.await_element(by.By.ID, "jobs__action_create job")

        action_column = driver.find_element_by_link_text(
            name).find_element_by_xpath('../../td[4]')
        action_column.find_element_by_link_text('More').click()
        action_column.find_element_by_link_text(
            'Launch On Existing Cluster').click()

        self.await_element(by.By.ID, "id_job_input")
        driver.find_element_by_xpath(
            "//select[@id='id_job_input']/option[text()='%s']" % input).click()
        driver.find_element_by_xpath(
            "//select[@id='id_job_output']/option[text()='%s']" %
            output).click()
        driver.find_element_by_xpath(
            "//select[@id='id_cluster']/option[text()='%s']" % cluster).click()

        if configure:
            driver.find_element_by_link_text('Configure').click()
            for config_part, values in configure.items():
                config_number = 1
                for config, value in values.items():
                    driver.find_element_by_id(
                        config_part).find_element_by_link_text('Add').click()
                    driver.find_element_by_xpath(
                        '//*[@id="%s"]/table/tbody/tr[%i]/td[1]/input' % (
                            config_part, config_number)).send_keys(config)
                    driver.find_element_by_xpath(
                        '//*[@id="%s"]/table/tbody/tr[%i]/td[2]/input' % (
                            config_part, config_number)).send_keys(value)
                    config_number += 1

        driver.find_element_by_xpath("//input[@value='Launch']").click()

        if not message:
            message = 'Success: Job launched'
        if close_window:
            self.check_create_object(name, positive, message,
                                     check_create_element=False)
        if await_launch:
            self.await_launch_job()

        else:
            self.error_helper(message)

    def delete_node_group_templates(self, names, undelete_names=None,
                                    finally_delete=False):
        url = "/project/data_processing/nodegroup_templates/"
        delete_button_id = 'nodegroup_templates__action_' \
                           'delete_nodegroup_template'
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete)

    def delete_cluster_templates(self, names, undelete_names=None,
                                 finally_delete=False):
        url = "/project/data_processing/cluster_templates/"
        delete_button_id = "cluster_templates__action_delete_cluster_template"
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete)

    def delete_clusters(self, names, undelete_names=None,
                        finally_delete=False):
        url = "/project/data_processing/clusters/"
        delete_button_id = "clusters__action_delete"
        msg = "Success: Deleted Cluster"
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete, succes_msg=msg)

    def delete_data_sources(self, names, undelete_names=None,
                            finally_delete=False):
        url = "/project/data_processing/data_sources/"
        delete_button_id = "data_sources__action_delete"
        msg = "Success: Deleted Data source"
        err_msg = 'Error: Unable to delete data source'
        info_msg = 'Info: Deleted Data source'
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete, msg, err_msg, info_msg)

    def delete_job_binaries(self, names, undelete_names=None,
                            finally_delete=False):

        url = "/project/data_processing/job_binaries/"
        delete_button_id = "job_binaries__action_delete"

        msg = "Success: Deleted Job binary"
        err_msg = 'Error: Unable to delete job binary'
        info_msg = 'Info: Deleted Job binary'

        if not undelete_names and len(names) > 1:
            msg = "Success: Deleted Job binarie"

        if undelete_names and len(names) - len(undelete_names) > 1:
            info_msg = 'Info: Deleted Job binarie'

        if undelete_names and len(undelete_names) > 1:
            err_msg = 'Error: Unable to delete job binarie'

        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete, msg, err_msg, info_msg)

    def delete_jobs(self, names, undelete_names=None, finally_delete=False):
        url = "/project/data_processing/jobs/"
        delete_button_id = "jobs__action_delete"
        msg = "Success: Deleted Job"
        err_msg = 'Error: Unable to delete job'
        info_msg = 'Info: Deleted Job'
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete, msg, err_msg, info_msg)

    def delete_all_job_executions(self):

        driver = self.driver
        driver.get(cfg.common.base_url +
                   "/project/data_processing/job_executions/")

        delete_button_id = 'job_executions__action_delete'

        self.await_element(by.By.ID, delete_button_id)

        if self.does_element_present(by.By.CLASS_NAME, 'multi_select_column'):

            if not driver.find_element_by_xpath(
                    '//*[@class=\'multi_select_column\']/input').is_selected():

                driver.find_element_by_class_name(
                    '//*[@class=\'multi_select_column\']/input').click()

            driver.find_element_by_id(delete_button_id).click()
            self.await_element(by.By.LINK_TEXT, 'Delete Job executions')
            driver.find_element_by_link_text('Delete Job executions').click()
            self.await_element(by.By.CLASS_NAME, "alert-success")
            message = 'Success: Deleted Job execution'
            actual_message = self.find_alert_message(
                "alert-success", first_character=2,
                last_character=len(message) + 2)
            self.assertEqual(actual_message, message)

    def unregister_images(self, names, undelete_names=[],
                          finally_delete=False):
        url = '/project/data_processing/data_image_registry/'
        delete_button_id = "image_registry__action_Unregister"
        msg = "Success: Unregistered Image"
        self.delete_and_validate(url, delete_button_id, names, undelete_names,
                                 finally_delete, succes_msg=msg,)

# -------------------------helpers_methods-------------------------------------

    @staticmethod
    def connect_to_swift():
        return swift_client.Connection(
            authurl=cfg.common.keystone_url,
            user=cfg.common.user,
            key=cfg.common.password,
            tenant_name=cfg.common.tenant,
            auth_version=2
        )

    @staticmethod
    def delete_swift_container(swift, container):

        objects = [obj['name'] for obj in swift.get_container(container)[1]]
        for obj in objects:

            swift.delete_object(container, obj)

        swift.delete_container(container)

    @classmethod
    def find_clear_send(cls, by_find, find_element, send):
        cls.driver.find_element(by=by_find, value=find_element).clear()
        cls.driver.find_element(by=by_find, value=find_element).send_keys(send)

    def click_visible_key(self, xpath):
        keys = self.driver.find_elements_by_xpath(xpath)
        for key in keys:
            if key.is_displayed():
                key.click()

    def delete_and_validate(self, url, delete_button_id, names, undelete_names,
                            finally_delete,
                            succes_msg='Success: Deleted Template',
                            error_msg='Error: Unable to delete template',
                            info_msg='Info: Deleted Template'):
        driver = self.driver
        driver.refresh()
        driver.get(cfg.common.base_url + url)
        self.await_element(by.By.ID, delete_button_id)
        for name in names:
            # choose checkbox for this element
            try:
                driver.find_element_by_link_text("%s" % name).\
                    find_element_by_xpath("../../td[1]/input").click()
            except selenim_except.NoSuchElementException as e:
                if finally_delete:
                    pass
                else:
                    print ('element with name %s not found for delete' % name)
                    raise e
        # click deletebutton
        driver.find_element_by_id(delete_button_id).click()
        # wait window to confirm the deletion
        self.await_element(by.By.CLASS_NAME, "btn-primary")
        # confirm the deletion
        driver.find_element_by_class_name("btn-primary").click()
        exp_del_obj = list(set(names).symmetric_difference(set(
            undelete_names if undelete_names else [])))
        if not undelete_names:
            if len(names) > 1:
                succes_msg += "s"
            succes_msg += ": "
            self.check_alert("alert-success", succes_msg, names, deleted=True)
        elif not exp_del_obj:
            if len(undelete_names) > 1:
                error_msg += "s"
            error_msg += ": "
            self.check_alert("alert-danger", error_msg, undelete_names,
                             deleted=False)
        else:
            if len(undelete_names) > 1:
                error_msg += "s"
            error_msg += ": "
            if len(exp_del_obj) > 1:
                info_msg += "s"
            info_msg += ": "
            self.check_alert("alert-danger", error_msg, undelete_names,
                             deleted=False)
            self.check_alert("alert-info", info_msg, exp_del_obj, deleted=True)
        driver.refresh()

    def error_helper(self, message):
        driver = self.driver
        messages = message.split(", ")
        self.await_element(by.By.CLASS_NAME, "error")
        errors = driver.find_elements_by_class_name("error")
        for message in messages:
            mes = message.split(":")
            if len(mes) > 1:
                # if word count for error mesage > 1, then error message
                #  can be on the open tab or on another
                if len(mes) > 2:
                    # if word count for error mesage > 2, then error message
                    #  on another tab
                    # Click the tab indicated in the message
                    driver.find_element_by_link_text(mes.pop(0)).click()
                error = errors.pop(0).text.split("\n")
                self.assertEqual(mes[0], error[0])
                self.assertEqual(mes[1], error[1])
            else:
                self.assertEqual(mes[0], errors.pop(0).text)
        self.assertEqual(errors, [])
        driver.refresh()

    def config_helper(self, config_list):
        driver = self.driver
        for pair in config_list:
            for par, value in pair.iteritems():
                if len(par.split(":")) > 1:
                    driver.find_element_by_link_text(par.split(":")[0]).click()
                    config_id = "id_CONF:%s" % par.split(":")[0].split(" ")[0]
                    if config_id == "id_CONF:General":
                        config_id = "id_CONF:general"
                    par = par.split(":")[1]
                if par == "Show_param":
                    if value:

                        self.waiting_element_in_visible_state(
                            by.By.LINK_TEXT, "Show full configuration")
                        driver.find_element_by_link_text(
                            "Show full configuration").click()
                        self.waiting_element_in_visible_state(
                            by.By.LINK_TEXT, "Hide full configuration")
                    else:
                        self.waiting_element_in_visible_state(
                            by.By.LINK_TEXT, "Hide full configuration")
                        driver.find_element_by_link_text(
                            "Hide full configuration").click()
                        self.waiting_element_in_visible_state(
                            by.By.LINK_TEXT, "Show full configuration")
                elif par == "Filter":
                    self.find_clear_send(
                        by.By.XPATH, "//input[@class='field-filter']", value)
                else:
                    self.waiting_element_in_visible_state(
                        by.By.ID, "%s:%s" % (config_id, par))
                    if isinstance(value, bool):
                        if driver.find_element_by_id(
                                "%s:%s" % (config_id,
                                           par)).is_selected() != value:
                            driver.find_element_by_id(
                                "%s:%s" % (config_id, par)).click()
                    else:
                        self.find_clear_send(
                            by.By.ID, "%s:%s" % (config_id, par), value)

    def image_registry_helper(self, image_name, user_name, description,
                              tags_to_add, tags_to_remove, positive,
                              close_window, message, operation):
        driver = self.driver
        list_for_check_tags = []
        driver.get(cfg.common.base_url +
                   "/project/data_processing/data_image_registry/")
        self.await_element(by.By.ID, "image_registry__action_register")
        if operation == 'Registry':
            driver.find_element_by_id(
                "image_registry__action_register").click()
        else:
            # Add existing tags in the list
            list_for_check_tags = driver.\
                find_element(by=by.By.LINK_TEXT, value=image_name).\
                find_element_by_xpath('../../td[3]').text.split('\n')
            # Click "Edit Tags"
            driver.find_element(by=by.By.LINK_TEXT, value=image_name).\
                find_element_by_xpath('../../td[4]').\
                find_element(by=by.By.LINK_TEXT, value='Edit Tags').click()
        self.await_element(by.By.ID, 'id_user_name')
        if operation == 'Registry':
            driver.find_element_by_xpath("//select[@id='id_image_id']"
                                         "/option[text()='%s']"
                                         % image_name).click()
        if user_name:
            self.find_clear_send(by.By.ID, 'id_user_name', user_name)
        if description:
            self.find_clear_send(by.By.ID, 'id_description', user_name)
        if tags_to_add:
            for tag in tags_to_add:
                for first, second in tag.iteritems():
                    if first in ["vanilla", 'hdp']:
                        driver.find_element_by_xpath(
                            "//select[@id='plugin_select']/option[text()='%s']"
                            % first).click()
                        driver.find_element_by_xpath(
                            "//select[@id='data_processing_version_%s']"
                            "/option[text()='%s']" % (first, second)).click()
                        driver.find_element_by_id('add_all_btn').click()
                        if first not in list_for_check_tags:
                            list_for_check_tags.append(first)
                        if second not in list_for_check_tags:
                            list_for_check_tags.append(second)
                    elif first == 'custom_tag':
                        self.find_clear_send(by.By.ID, '_sahara_image_tag',
                                             second)
                        driver.find_element_by_id('add_tag_btn').click()
                        if second not in list_for_check_tags:
                            list_for_check_tags.append(second)
                    else:
                        self.fail("Tag:%s, %s is unknown" % (first, second))
        if tags_to_remove:
            for tag in tags_to_remove:
                # click "x" in tag
                driver.find_element_by_xpath(
                    "//div[@id='image_tags_list']//span[contains(.,'%s')]//i"
                    % tag).click()
                if tag in list_for_check_tags:
                    list_for_check_tags.remove(tag)
        driver.find_element_by_id('edit_image_tags_btn').click()
        if positive:
            self.check_create_object(image_name, positive, message,
                                     [{3: list_for_check_tags}])
        else:
            if not close_window:
                self.error_helper(message)
            else:
                self.check_create_object(image_name, positive, message)

    def choose_plugin_name(self, plugin_name, hadoop_version, name,
                           description, id_name):
        self.await_element(by.By.ID, "id_plugin_name")
        self.driver.find_element_by_xpath(
            "//select[@id='id_plugin_name']/option[text()='%s']" %
            plugin_name).click()
        if plugin_name == "Hortonworks Data Platform":
            version_id = "id_hdp_version"
        elif plugin_name == "Vanilla Apache Hadoop":
            version_id = "id_vanilla_version"
        else:
            self.fail("plugin_name:%s is wrong" % plugin_name)
        self.driver.find_element_by_id(version_id).find_element_by_xpath(
            "option[text()='%s']" % hadoop_version).click()
        self.driver.find_element_by_xpath("//input[@value='Create']").click()
        self.await_element(by.By.ID, id_name)
        self.find_clear_send(by.By.ID, id_name, name)
        if description:
            self.find_clear_send(by.By.ID, "id_description", description)

    def check_alert(self, alert, expected_message, list_obj, deleted=True):
        self.await_element(by.By.CLASS_NAME, alert)
        actual_message = self.find_alert_message(
            alert, first_character=2, last_character=len(expected_message) + 2)
        self.assertEqual(actual_message, expected_message)
        not_expected_objs = list(set(self.find_alert_message(
            alert, first_character=len(expected_message) + 2).split(
                ", ")).symmetric_difference(set(list_obj)))
        if not_expected_objs:
            self.fail("have deleted objects: %s" % not_expected_objs)
        for name in list_obj:
            if self.does_element_present(by.By.LINK_TEXT, name) == deleted:
                if deleted:
                    errmsg = "object with name:%s is not deleted" % name
                else:
                    errmsg = "object with name:%s is deleted" % name
                self.fail(errmsg)

    def find_alert_message(self, name, first_character=None,
                           last_character=None):
        driver = self.driver
        return str(driver.find_element_by_class_name("%s" % name).text[
                   first_character:last_character])

    def search_id_processes(self, process, plugin):
        return plugin.processes[process]

    def waiting_element_in_visible_state(self, how, what):
        for i in range(cfg.common.await_element):
            if self.driver.find_element(by=how, value=what).is_displayed():
                break
            time.sleep(1)
        else:
            self.fail("time out for await visible: %s , %s" % (how, what))

    def does_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except Exception as e:
            print(e.message)
            return False
        return True

    def await_element(self, by, value, message=""):
        for i in range(cfg.common.await_element):
            if self.does_element_present(by, value):
                break
            time.sleep(1)
        else:
            if not message:
                message = "time out for await: %s , %s" % (by, value)
            self.fail(message)

    def check_create_object(self, name, positive, expected_message,
                            check_columns=None, check_create_element=True):
        driver = self.driver
        expected_alert = "alert-danger"
        unexpected_alert = "alert-success"
        if positive:
            expected_alert = "alert-success"
            unexpected_alert = "alert-danger"
        for i in range(cfg.common.await_element):
            if self.does_element_present(by.By.CLASS_NAME, expected_alert):
                break
            elif self.does_element_present(by.By.CLASS_NAME, unexpected_alert):
                fail_mesg = self.driver.find_element(
                    by=by.By.CLASS_NAME, value=unexpected_alert).text[2:]
                self.fail("Result of creation %s is not expected: %s != %s"
                          % (name, expected_message, fail_mesg))
            time.sleep(1)
        else:
            self.fail("alert check:%s time out" % expected_alert)
        actual_message = self.driver.find_element(
            by=by.By.CLASS_NAME, value=expected_alert).text[2:]
        if check_create_element and positive:
            self.assertEqual(expected_message, str(actual_message))
            if not self.does_element_present(by.By.LINK_TEXT, name):
                self.fail("object with name:%s not found" % name)
            if check_columns:
                for column in check_columns:
                    for column_number, expected_values in column.iteritems():
                        actual_values = driver.\
                            find_element_by_link_text(name).\
                            find_element_by_xpath(
                                '../../td[%d]' % column_number).\
                            text.split('\n')
                        self.assertItemsEqual(actual_values, expected_values)
        else:
            if expected_message:
                self.assertEqual(expected_message, str(actual_message))
        self.driver.refresh()

    def await_cluster_active(self, name):
        driver = self.driver
        i = 1
        while True:

            if i > cfg.common.cluster_creation_timeout * 60:
                self.fail(
                    'cluster is not getting status \'Active\', '
                    'passed %d minutes' % cfg.common.cluster_creation_timeout)

            try:
                status = driver.find_element_by_link_text(
                    "selenium-cl").find_element_by_xpath("../../td[3]").text
            except selenim_except.StaleElementReferenceException:
                status = 'unknown'

            if str(status) == 'Error':
                self.fail('Cluster state == \'Error\'.')

            if str(status) == 'Active':
                break

            time.sleep(5)
            i += 5

    def await_launch_job(self):
        driver = self.driver
        driver.get(cfg.common.base_url +
                   "/project/data_processing/job_executions/")
        self.await_element(by.By.ID, 'job_executions')

        job_id = driver.find_element_by_id(
            'job_executions').find_elements_by_class_name(
                'ajax-update')[-1].get_attribute('id')

        status = driver.find_element_by_xpath(
            '//*[@id="%s"]/td[3]' % job_id).text
        timeout = cfg.common.job_launch_timeout * 60

        while str(status) != 'SUCCEEDED':

            if timeout <= 0:
                self.fail(
                    'Job did not return to \'SUCCEEDED\' status within '
                    '%d minute(s).' % cfg.common.job_launch_timeout)

            if status == 'KILLED':
                self.fail('Job status == \'KILLED\'.')

            status = driver.find_element_by_xpath(
                '//*[@id="%s"]/td[3]' % job_id).text
            time.sleep(1)
            timeout -= 1

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
