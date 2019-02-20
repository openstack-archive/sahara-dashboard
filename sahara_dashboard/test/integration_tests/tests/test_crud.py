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

from sahara_dashboard.test.integration_tests.helpers import SaharaTestCase


PLUGIN_NAME = 'Fake Plugin'
PLUGIN_VERSION = '0.1'

IMAGE_TAGS = ('fake', PLUGIN_VERSION)


class TestCRUDBase(SaharaTestCase):

    def setUp(self):
        super(TestCRUDBase, self).setUp()
        self.flavor_name = self.gen_name('flavor')
        self.image_name = self.gen_name("image")
        self.master_name = self.gen_name("master")
        self.worker_name = self.gen_name("worker")
        self.template_name = self.gen_name("template")
        self.cluster_name = self.gen_name("cluster")
        self.ds_input_name = self.gen_name('input')
        self.ds_output_name = self.gen_name('output')
        self.job_binary_name = self.gen_name('function')
        self.jobtemplate_name = self.gen_name('test-job')

    def create_flavor(self):
        flavors_page = self.home_pg.go_to_admin_compute_flavorspage()

        flavors_page.create_flavor(
            name=self.flavor_name,
            vcpus=self.CONFIG.sahara.flavor_vcpus,
            ram=self.CONFIG.sahara.flavor_ram,
            root_disk=self.CONFIG.sahara.flavor_root_disk,
            ephemeral_disk=self.CONFIG.sahara.flavor_ephemeral_disk,
            swap_disk=self.CONFIG.sahara.flavor_swap_disk)
        self.assertTrue(flavors_page.is_flavor_present(self.flavor_name))

    def delete_flavor(self):
        flavors_page = self.home_pg.go_to_admin_compute_flavorspage()
        flavors_page.delete_flavor_by_row(self.flavor_name)
        self.assertFalse(flavors_page.is_flavor_present(self.flavor_name))

    def create_image(self):
        image_pg = self.home_pg.go_to_project_compute_imagespage()
        image_pg.create_image(
            self.image_name, image_file=self.CONFIG.sahara.fake_image_location)
        image_pg._wait_until(
            lambda x: image_pg.is_image_active(self.image_name),
            timeout=10 * 60)

    def delete_image(self):
        image_pg = self.home_pg.go_to_project_compute_imagespage()
        image_pg.delete_image(self.image_name)

    def register_image(self):
        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_ssh_user = self.CONFIG.sahara.fake_image_ssh_user
        image_reg_pg.register_image(self.image_name, image_ssh_user,
                                    "Test description", tags=IMAGE_TAGS)
        image_reg_pg.wait_until_image_registered(self.image_name)

    def unregister_image(self):
        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_reg_pg.unregister_image(self.image_name)

    def create_cluster(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )

        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.worker_name,
            floating_ip_pool=self.CONFIG.sahara.ip_pool,
            flavor=self.flavor_name, processes=['tasktracker', 'datanode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.worker_name),
                        "Worker template was not created.")

        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())

        clustertpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, name=self.template_name,
            node_group_templates=[self.master_name, self.worker_name])
        self.assertTrue(clustertpls_pg.has_success_message())
        self.assertFalse(clustertpls_pg.has_error_message())
        self.assertTrue(clustertpls_pg.is_present(self.template_name),
                        "Cluster template was not created.")

        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.create(PLUGIN_NAME, PLUGIN_VERSION, name=self.cluster_name,
                          image=self.image_name,
                          cluster_template=self.template_name)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())
        cluster_pg.refresh_page()
        self.assertTrue(cluster_pg.is_present(self.cluster_name),
                        "Cluster was not created.")

        cluster_pg.wait_until_cluster_active(
            self.cluster_name, timeout=self.CONFIG.sahara.launch_timeout)
        self.assertTrue(cluster_pg.is_cluster_active(self.cluster_name),
                        "Cluster is not active")

    def cluster_scale(self):
        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.scale(self.cluster_name, self.worker_name, 2)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())

        cluster_pg.wait_until_cluster_active(
            self.cluster_name, timeout=self.CONFIG.sahara.launch_timeout)
        self.assertTrue(cluster_pg.is_cluster_active(self.cluster_name),
                        "Cluster is not active")
        self.assertEqual(
            cluster_pg.get_cluster_instances_count(self.cluster_name), 2,
            "Cluster was not scaled")

    def create_datasources(self):
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        datasource_pg.create(name=self.ds_input_name, source_type="HDFS",
                             url="hdfs://user/input")
        datasource_pg.create(name=self.ds_output_name, source_type="Swift",
                             url="swift://container/output")

    def delete_datasources(self):
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        datasource_pg.delete(self.ds_input_name)
        datasource_pg.delete(self.ds_output_name)

    def create_job_binary(self):
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        job_binary_pg.create_job_binary_from_file(
            self.job_binary_name, __file__)

        self.assertTrue(
            job_binary_pg.is_job_binary_present(self.job_binary_name),
            "Job binary is not in the binaries job table after its creation.")

    def delete_job_binary(self):
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        job_binary_pg.delete_job_binary(self.job_binary_name)
        self.assertFalse(
            job_binary_pg.is_job_binary_present(self.job_binary_name),
            "Job binary was not removed from binaries job table.")

    def create_job_template(self):
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.create(name=self.jobtemplate_name, job_type='Pig',
                               binary_name=self.job_binary_name)

    def delete_job_template(self):
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.delete(self.jobtemplate_name)

    def run_edp_job(self):
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.launch_on_exists(job_name=self.jobtemplate_name,
                                         input_name=self.ds_input_name,
                                         output_name=self.ds_output_name,
                                         cluster_name=self.cluster_name)
        jobs_pg = self.home_pg.go_to_dataprocessing_jobs_jobspage()
        jobs_pg.wait_until_job_succeeded(self.jobtemplate_name)

    def run_edp_job_with_parameters(self):
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.launch_on_exists(job_name=self.jobtemplate_name,
                                         input_name=self.ds_input_name,
                                         output_name=self.ds_output_name,
                                         cluster_name=self.cluster_name,
                                         adapt_swift=False,
                                         datasource_substitution=False,
                                         configuration={'foo': 'bar'},
                                         parameters={'key': 'value'},
                                         arguments=('one', 'two'))
        jobs_pg = self.home_pg.go_to_dataprocessing_jobs_jobspage()
        details = jobs_pg.get_details(self.jobtemplate_name)
        expected = {
            'Job Configuration': {
                'configs': set([
                    'edp.substitute_data_source_for_name = False',
                    'foo = bar',
                    'edp.substitute_data_source_for_uuid = False'
                ]),
                'params': set(['key = value']),
                'args': set(['one', 'two']),
                'job_execution_info': set([]),
            },
            'Job Template': self.jobtemplate_name,
        }

        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def delete_job(self):
        jobs_pg = self.home_pg.go_to_dataprocessing_jobs_jobspage()
        jobs_pg.delete(self.jobtemplate_name)

    def delete_cluster(self):
        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.delete(self.cluster_name)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())
        cluster_pg.wait_until_cluster_deleted(self.cluster_name)
        self.assertFalse(cluster_pg.is_present(self.cluster_name),
                         "Cluster was not deleted.")

    def tearDown(self):
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        if clustertpls_pg.is_present(self.template_name):
            clustertpls_pg.delete(self.template_name)

        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        nodegrouptpls_pg.delete_many((self.worker_name, self.master_name))
        super(TestCRUDBase, self).tearDown()


class TestCRUD(TestCRUDBase):

    def setUp(self):
        super(TestCRUD, self).setUp()
        self.create_flavor()
        self.create_image()
        self.register_image()

    def run_many_edp_jobs(self):
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        job_names = {}
        for job_type in ("Hive", "Java", "MapReduce", "Streaming MapReduce",
                         "Pig", "Shell", "Spark", "Storm"):
            job_name = "{0}-{1}".format(self.jobtemplate_name, job_type)
            job_name = job_name.replace(' ', '-')
            job_names[job_type] = job_name
            binary_name = self.job_binary_name
            libs = []
            if job_type in ("Java", "MapReduce", "Streaming MapReduce"):
                binary_name = None
                libs.append(self.job_binary_name)
            jobtemplates_pg.create(name=job_name, job_type=job_type,
                                   binary_name=binary_name, libs=libs)

        for job_type, job_name in job_names.items():
            jobtemplates_pg = (
                self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
            input_name = self.ds_input_name
            output_name = self.ds_output_name
            mapper = None
            reducer = None
            if job_type in ("Java", "Shell", "Storm", "Spark"):
                input_name = None
                output_name = None
            if job_type == "Streaming MapReduce":
                mapper = "mapper"
                reducer = "reducer"
            jobtemplates_pg.launch_on_exists(job_name=job_name,
                                             input_name=input_name,
                                             output_name=output_name,
                                             cluster_name=self.cluster_name,
                                             mapper=mapper,
                                             reducer=reducer)
            jobs_pg = self.home_pg.go_to_dataprocessing_jobs_jobspage()
            jobs_pg.wait_until_job_succeeded(job_name)

        jobs_pg.delete_many(job_names.values())

        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.delete_many(job_names.values())

    def test_cluster_operate(self):
        self.create_cluster()
        self.create_datasources()
        self.create_job_binary()
        self.create_job_template()
        self.run_edp_job()
        self.delete_job()
        self.run_edp_job_with_parameters()
        self.delete_job()
        self.run_many_edp_jobs()
        self.delete_job_template()
        self.delete_job_binary()
        self.delete_datasources()
        self.cluster_scale()
        self.delete_cluster()

    def tearDown(self):
        self.unregister_image()
        self.delete_image()
        self.delete_flavor()
        super(TestCRUD, self).tearDown()


class TestUpdateNodeGroupTemplate(SaharaTestCase):
    def setUp(self):
        super(TestUpdateNodeGroupTemplate, self).setUp()
        self.old_name = self.gen_name("old-name")
        self.new_name = self.gen_name("new-name")
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )

        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.old_name,
            flavor='m1.tiny', processes=['tasktracker', 'datanode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.old_name),
                        "Worker template was not created.")

    def test_update(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        kwargs = {
            'nodegroup_name': self.new_name,
            'description': '{} description'.format(self.new_name),
            'flavor': 'm1.small',
            'availability_zone': 'No availability zone specified',
            'storage': 'Cinder Volume',
            'volumes_per_node': 2,
            'volumes_size': 3,
            'volume_type': 'lvmdriver-1',
            'volume_local_to_instance': True,
            'volumes_availability_zone': 'nova',
            'floating_ip_pool': self.CONFIG.sahara.ip_pool,
            'use_autoconfig': False,
            'proxygateway': True,
            'processes': ['jobtracker', 'namenode'],
            'security_autogroup': False,
            'security_groups': ['default']
        }
        nodegrouptpls_pg.update(group_name=self.old_name, **kwargs)
        details = nodegrouptpls_pg.get_details(self.new_name)
        expected = {
            'Auto Security Group': 'False',
            'Description': kwargs['description'],
            'Flavor': 'm1.small',
            'Floating IP Pool': self.CONFIG.sahara.ip_pool,
            'Name': self.new_name,
            'Node Processes': 'namenode\njobtracker',
            'Plugin': 'fake',
            'Proxy Gateway': 'True',
            'Security Groups': 'default',
            'Use auto-configuration': 'False',
            'Version': '0.1',
            'Volumes Availability Zone': 'nova',
            'Volumes local to instance': 'True',
            'Volumes per node': '2',
            'Volumes size': '3',
            'Volumes type': 'lvmdriver-1'
        }
        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def tearDown(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        nodegrouptpls_pg.delete_many((self.old_name, self.new_name))
        super(TestUpdateNodeGroupTemplate, self).tearDown()


class TestUpdateClusterTemplate(SaharaTestCase):
    def setUp(self):
        super(TestUpdateClusterTemplate, self).setUp()
        self.flavor_name = self.gen_name('flavor')
        self.image_name = self.gen_name("image")

        self.worker_name = self.gen_name("worker")
        self.new_worker_name = self.gen_name("new-worker")
        self.master_name = self.gen_name("master")
        self.cluster_template_name = self.gen_name("old-name")
        self.new_cluster_template_name = self.gen_name("new-name")

        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )

        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.worker_name,
            flavor='m1.tiny', processes=['tasktracker', 'datanode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.worker_name),
                        "Worker template was not created.")
        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.master_name,
            flavor='m1.tiny', proxygateway=True,
            floating_ip_pool=self.CONFIG.sahara.ip_pool,
            processes=['jobtracker', 'namenode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.master_name),
                        "Worker template was not created.")
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())

        clustertpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, name=self.cluster_template_name,
            node_group_templates=[self.worker_name])
        self.assertTrue(clustertpls_pg.has_success_message())
        self.assertFalse(clustertpls_pg.has_error_message())
        self.assertTrue(clustertpls_pg.is_present(self.cluster_template_name),
                        "Cluster template was not created.")

    def test_update(self):
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        kwargs = {
            'cluster_template_name': self.new_cluster_template_name,
            'description': '{} description'.format(
                self.new_cluster_template_name),
            'use_autoconfig': False,
            'anti_affinity': ['namenode', 'datanode', 'tasktracker',
                              'jobtracker'],
            'node_group_templates': [self.master_name],
            'CONF:general:Timeout for disk preparing': 152,
            'CONF:general:Enable NTP service': False,
            'CONF:general:URL of NTP server': 'http://ntp.org/',
            'CONF:general:Heat Wait Condition timeout': 123,
            'CONF:general:Enable XFS': False,
        }
        clustertpls_pg.update(name=self.cluster_template_name, **kwargs)
        self.assertTrue(clustertpls_pg.has_success_message())
        self.assertFalse(clustertpls_pg.has_error_message())
        self.assertTrue(
            clustertpls_pg.is_present(self.new_cluster_template_name),
            "Cluster template was not updated.")
        details = clustertpls_pg.get_details(self.new_cluster_template_name)

        expected = {
            'Name': self.new_cluster_template_name,
            'Description': kwargs['description'],
            'Plugin': 'fake',
            'Version': '0.1',
            'Use auto-configuration': 'False',
            'Anti-affinity enabled for': set(['namenode', 'datanode',
                                              'tasktracker', 'jobtracker']),
            'Enable NTP service': 'False',
            'Enable XFS': 'False',
            'Heat Wait Condition timeout': '123',
            'Timeout for disk preparing': '152',
            'URL of NTP server': 'http://ntp.org/',
            'node_groups': {
                self.master_name: '1'
            }
        }
        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def test_update_nodegroup(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        kwargs = {
            'nodegroup_name': self.new_worker_name,
            'description': '{} description'.format(self.new_worker_name),
            'flavor': 'm1.small',
            'availability_zone': 'No availability zone specified',
            'floating_ip_pool': 'public',
            'use_autoconfig': False,
            'proxygateway': True,
            'processes': ['jobtracker', 'namenode'],
            'security_autogroup': False,
            'security_groups': ['default']
        }
        nodegrouptpls_pg.update(group_name=self.worker_name, **kwargs)
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.new_worker_name),
                        "Node group template was not updated.")
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        details = clustertpls_pg.get_nodegroup_details(
            self.cluster_template_name, self.new_worker_name)
        expected = {
            'Auto Security Group': 'no',
            'Flavor': '2',
            'Node Processes': {'namenode', 'jobtracker'},
            'Nodes Count': '1',
            'Proxy Gateway': 'yes',
            'Security Groups': 'default',
            'Template': self.new_worker_name,
            'Use auto-configuration': 'False'
        }
        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def tearDown(self):
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        clustertpls_pg.delete_many((self.cluster_template_name,
                                    self.new_cluster_template_name))

        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        nodegrouptpls_pg.delete_many((self.worker_name, self.master_name,
                                      self.new_worker_name))
        super(TestUpdateClusterTemplate, self).tearDown()


class TestUpdateDataSource(SaharaTestCase):

    def setUp(self):
        super(TestUpdateDataSource, self).setUp()
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        self.name = self.gen_name('input')
        self.new_name = '{}-new'.format(self.name)
        datasource_pg.create(name=self.name, source_type="HDFS",
                             url="hdfs://user/input")

    def test_update(self):
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        kwargs = {
            'data_source_name': self.new_name,
            'data_source_type': 'Swift',
            'data_source_url': 'swift://container.sahara/object',
            'data_source_credential_user': 'test-user',
            'data_source_credential_pass': 'test-password',
            'data_source_description': '{} description'.format(self.new_name),
        }
        datasource_pg.update(self.name, **kwargs)
        self.assertTrue(datasource_pg.has_success_message())
        self.assertFalse(datasource_pg.has_error_message())
        self.assertTrue(datasource_pg.is_present(self.new_name),
                        "Node group template was not updated.")
        details = datasource_pg.get_details(self.new_name)
        expected = {
            'Description': kwargs['data_source_description'],
            'Name': self.new_name,
            'Type': 'swift',
            'URL': 'swift://container.sahara/object'
        }
        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def tearDown(self):
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        datasource_pg.delete_many([self.name, self.new_name])
        super(TestUpdateDataSource, self).tearDown()


class TestUpdateJobBinaries(SaharaTestCase):

    def setUp(self):
        super(TestUpdateJobBinaries, self).setUp()
        # create job binary
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        self.name = self.gen_name('function')
        self.new_name = '{}-new'.format(self.name)
        job_binary_pg.create_job_binary_from_file(self.name, __file__)

    def test_update(self):
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        kwargs = {
            "job_binary_name": self.new_name,
            "job_binary_type": "Internal database",
            "job_binary_internal": "*Create a script",
            "job_binary_script_name": "script-name",
            "job_binary_script": "script-text",
            "job_binary_description": "{} description".format(self.new_name),
        }
        job_binary_pg.update_job_binary(self.name, **kwargs)
        self.assertTrue(job_binary_pg.has_success_message())
        self.assertFalse(job_binary_pg.has_error_message())
        self.assertTrue(job_binary_pg.is_job_binary_present(self.new_name),
                        "Job binary was not updated.")
        details = job_binary_pg.get_details(self.new_name)
        expected = {
            'Description': kwargs['job_binary_description'],
            'Name': self.new_name,
        }

        details = {k: v for k, v in details.items() if k in expected}
        self.assertEqual(expected, details)

    def tearDown(self):
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        for name in (self.name, self.new_name):
            try:
                job_binary_pg.delete_job_binary(name)
            except Exception:
                pass
        super(TestUpdateJobBinaries, self).tearDown()
