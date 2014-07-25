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

import os

from oslo.config import cfg

common_group = cfg.OptGroup(name='common', title="common configs")

CommonGroup = [
    cfg.StrOpt('base_url',
               default='http://127.0.0.1:8080',
               help="sahara url"),
    cfg.StrOpt('user',
               default='admin',
               help="keystone user"),
    cfg.StrOpt('password',
               default='pass',
               help="password for keystone user"),
    cfg.StrOpt('keypair',
               default='public-jenkins',
               help='keypair for create cluster'),
    cfg.StrOpt('tenant',
               default='admin',
               help='keystone tenant'),
    cfg.BoolOpt('auto_security_groups',
                default=False,
                help="Security Groups for sahara cluster"),
    cfg.ListOpt('security_groups',
                default=None,
                help="Security Groups for sahara cluster"),
    cfg.StrOpt('flavor',
               default='m1.minniemouse',
               help='OpenStack flavor name for image.'),
    cfg.StrOpt('neutron_management_network',
               default=None,
               help='Private network for quantum.'
                    'Must be specified in create cluster tab'),
    cfg.StrOpt('floating_ip_pool',
               default=None,
               help='Public network for quantum.'
                    'Must be specified in create nodegroup template tab'),
    cfg.StrOpt('keystone_url',
               default='http://127.0.0.1:5000/v2.0',
               help='url for keystone authentication'),
    cfg.BoolOpt('anty_affinity',
                default=False,
                help="Parameter for enable/disable Anty Affinity "
                     "Groups for Sahara cluster"),
    cfg.BoolOpt('cinder',
                default=False,
                help="Parameter for enable/disable attach volume disk "
                     "to node for Sahara cluster"),
    cfg.IntOpt('cluster_creation_timeout',
               default=10,
               help="cluster timeout in minutes"),
    cfg.IntOpt('await_element',
               default=15,
               help="await each web element in seconds"),
    cfg.StrOpt('image_name_for_register',
               default='fedora_19',
               help='Image name for register to Sahara'),
    cfg.StrOpt('image_name_for_edit',
               default='latest-ci-image',
               help='Image name for edit in image registry in Sahara'),
    cfg.IntOpt('job_launch_timeout',
               default=5,
               help='Timeout for job launch (in minutes); '
                    'minimal value is 1.'),
]

vanilla_group = cfg.OptGroup(name='vanilla', title="vanilla configs")

VanillaGroup = [
    cfg.BoolOpt('skip_plugin_tests',
                default=False,
                help="""
                If this variable is True then
                tests for vanilla will be skipped
                """),
    cfg.BoolOpt('skip_edp_test', default=True),
    cfg.StrOpt('plugin_name',
               default='Vanilla Apache Hadoop',
               help="plugin title, default: Vanilla Apache Hadoop"),
    cfg.StrOpt('plugin_overview_name',
               default='vanilla',
               help="plugin name in overview"),
    cfg.StrOpt('cluster_name',
               default="selenium-cl",
               help="Name of vanilla cluster"),
    cfg.StrOpt('hadoop_version',
               default='1.2.1',
               help="hadoop version for plugin"),
    cfg.DictOpt('processes',
                default={"NN": 0, "DN": 1, "SNN": 2,
                         "OZ": 3, "TT": 4, "JT": 5, "hiveserver": 6},
                help='numbers of processes for vanilla in saharadashboard'),
    cfg.StrOpt('base_image',
               default='ubuntu_sahara_latest',
               help="image name for start vanilla cluster")
]

hdp_group = cfg.OptGroup(name='hdp', title="hdp configs")

HdpGroup = [
    cfg.BoolOpt('skip_plugin_tests',
                default=False,
                help="""
                If this variable is True then
                tests for hdp will be skipped
                """),
    cfg.StrOpt('plugin_name',
               default='Hortonworks Data Platform',
               help="plugin title, default: Hortonworks Data Platform"),
    cfg.StrOpt('plugin_overview_name',
               default='hdp',
               help="plugin name in overview"),
    cfg.StrOpt('hadoop_version',
               default='1.3.2',
               help="hadoop version for plugin"),
    cfg.DictOpt('processes',
                default={
                    "NN": 0, "DN": 1, "SNN": 2, "HDFS_CLIENT": 3,
                    " ZOOKEEPER_SERVER": 4, "ZOOKEEPER_CLIENT": 5,
                    "AMBARI_SERVER": 6, "HCAT": 7, "SQOOP": 8,
                    "JT": 9, "TT": 10, "MAPREDUCE_CLIENT": 11,
                    "HIVE_SERVER": 12, "HIVE_METASTORE": 13,
                    "HIVE_CLIENT": 14, "MYSQL_SERVER": 15,
                    "PIG": 16, "WEBHCAT_SERVER": 17, "OOZIE_SERVER": 18,
                    "OOZIE_CLIENT": 19, "GANGLIA_SERVER": 20,
                    "NAGIOS_SERVER": 21, "HBASE_MASTER": 22,
                    "HBASE_REGIONSERVER": 23, "HBASE_CLIENT": 24
                }, help='numbers of processes for hdp in saharadashboard'),
    cfg.StrOpt('base_image',
               default='ib-centos-6-4-64-hdp-13',
               help="image name for start hdp cluster")
]


def register_config(config, config_group, config_opts):

    config.register_group(config_group)
    config.register_opts(config_opts, config_group)

path = os.path.join("%s/saharadashboard/tests/configs/config.conf"
                    % os.getcwd())

if os.path.exists(path):
    cfg.CONF([], project='saharadashboard', default_config_files=[path])

register_config(cfg.CONF, common_group, CommonGroup)
register_config(cfg.CONF, vanilla_group, VanillaGroup)
register_config(cfg.CONF, hdp_group, HdpGroup)

common = cfg.CONF.common
vanilla = cfg.CONF.vanilla
hdp = cfg.CONF.hdp
