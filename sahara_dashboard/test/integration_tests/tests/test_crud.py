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


class TestCRUD(SaharaTestCase):

    def setUp(self):
        super(TestCRUD, self).setUp()
        self.flavor_name = self.gen_name('flavor')
        self.image_name = self.gen_name("image")
        self.master_name = self.gen_name("master")
        self.worker_name = self.gen_name("worker")
        self.template_name = self.gen_name("template")
        self.cluster_name = self.gen_name("cluster")

        flavors_page = self.home_pg.go_to_system_flavorspage()
        flavors_page.create_flavor(
            name=self.flavor_name,
            vcpus=self.CONFIG.sahara.flavor_vcpus,
            ram=self.CONFIG.sahara.flavor_ram,
            root_disk=self.CONFIG.sahara.flavor_root_disk,
            ephemeral_disk=self.CONFIG.sahara.flavor_ephemeral_disk,
            swap_disk=self.CONFIG.sahara.flavor_swap_disk)

        self.assertTrue(flavors_page.is_flavor_present(self.flavor_name))
        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.create_image(self.image_name,
                              location=self.CONFIG.sahara.fake_http_image)
        image_pg.wait_until_image_active(self.image_name)
        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_ssh_user = self.CONFIG.sahara.fake_image_ssh_user
        image_reg_pg.register_image(self.image_name, image_ssh_user,
                                    "Test description", tags=IMAGE_TAGS)
        image_reg_pg.wait_until_image_registered(self.image_name)

    def create_cluster(self):
        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )

        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.worker_name,
            flavor=self.flavor_name, processes=['tasktracker', 'datanode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.worker_name),
                        "Worker template was not created.")
        nodegrouptpls_pg.create(
            PLUGIN_NAME, PLUGIN_VERSION, nodegroup_name=self.master_name,
            flavor=self.flavor_name,
            proxygateway=True, floating_ip_pool=self.CONFIG.sahara.ip_pool,
            processes=['jobtracker', 'namenode'])
        self.assertTrue(nodegrouptpls_pg.has_success_message())
        self.assertFalse(nodegrouptpls_pg.has_error_message())
        self.assertTrue(nodegrouptpls_pg.is_present(self.master_name),
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
            cluster_pg.get_cluster_instances_count(self.cluster_name), 3,
            "Cluster was not scaled")

    def run_edp_job(self):
        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        input_name = self.gen_name('input')
        datasource_pg.create(name=input_name, source_type="HDFS",
                             url="hdfs://user/input")
        output_name = self.gen_name('output')
        datasource_pg.create(name=output_name, source_type="Swift",
                             url="swift://container/output")

        # create job binary
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        job_binary_name = self.gen_name('function')
        job_binary_pg.create_job_binary_from_file(job_binary_name, __file__)

        self.assertTrue(job_binary_pg.is_job_binary_present(job_binary_name),
                        "Job binary is not in the binaries job table after"
                        " its creation.")

        # create job template
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplate_name = self.gen_name('test-job')
        jobtemplates_pg.create(name=jobtemplate_name, job_type='Pig',
                               binary_name=job_binary_name)

        # launch job
        jobtemplates_pg.launch_on_exists(job_name=jobtemplate_name,
                                         input_name=input_name,
                                         output_name=output_name,
                                         cluster_name=self.cluster_name)
        jobs_pg = self.home_pg.go_to_dataprocessing_jobs_jobspage()
        jobs_pg.wait_until_job_succeeded(jobtemplate_name)

        # delete job
        jobs_pg.delete(jobtemplate_name)

        # delete job_template
        jobtemplates_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobtemplatespage())
        jobtemplates_pg.delete(jobtemplate_name)

        # delete job binary
        job_binary_pg = (
            self.home_pg.go_to_dataprocessing_jobs_jobbinariespage())
        job_binary_pg.delete_job_binary(job_binary_name)
        self.assertFalse(job_binary_pg.is_job_binary_present(job_binary_name),
                         "Job binary was not removed from binaries job table.")

        datasource_pg = (
            self.home_pg.go_to_dataprocessing_jobs_datasourcespage())
        datasource_pg.delete(input_name)
        datasource_pg.delete(output_name)

    def delete_cluster(self):
        cluster_pg = self.home_pg.go_to_dataprocessing_clusters_clusterspage()
        cluster_pg.delete(self.cluster_name)
        self.assertTrue(cluster_pg.has_success_message())
        self.assertFalse(cluster_pg.has_error_message())
        cluster_pg.wait_until_cluster_deleted(self.cluster_name)
        self.assertFalse(cluster_pg.is_present(self.cluster_name),
                         "Cluster was not deleted.")

    def test_cluster_operate(self):
        self.create_cluster()
        self.run_edp_job()
        self.cluster_scale()
        self.delete_cluster()

    def tearDown(self):
        clustertpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_clustertemplatespage())
        if clustertpls_pg.is_present(self.template_name):
            clustertpls_pg.delete(self.template_name)

        nodegrouptpls_pg = (
            self.home_pg.go_to_dataprocessing_clusters_nodegrouptemplatespage()
        )
        nodegrouptpls_pg.delete_many((self.worker_name, self.master_name))

        image_reg_pg = (
            self.home_pg.go_to_dataprocessing_clusters_imageregistrypage())
        image_reg_pg.unregister_image(self.image_name)

        image_pg = self.home_pg.go_to_compute_imagespage()
        image_pg.delete_image(self.image_name)

        flavors_page = self.home_pg.go_to_system_flavorspage()
        flavors_page.delete_flavor(self.flavor_name)
        self.assertFalse(flavors_page.is_flavor_present(self.flavor_name))
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
