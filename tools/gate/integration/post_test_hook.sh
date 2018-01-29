#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

set -x
. commons $@

set +e
cd /opt/stack/new/sahara-dashboard

sudo wget -q -O firefox.deb https://sourceforge.net/projects/ubuntuzilla/files/mozilla/apt/pool/main/f/firefox-mozilla-build/firefox-mozilla-build_46.0.1-0ubuntu1_amd64.deb/download
sudo apt-get -y purge firefox
sudo dpkg -i firefox.deb
sudo rm firefox.deb

cat >> /tmp/fake_config.json <<EOF
{
    "plugin_labels": {
        "hidden": {
            "status": false
        }
    }
}
EOF

. $DEVSTACK_DIR/stackrc
. $DEVSTACK_DIR/openrc admin demo

openstack dataprocessing plugin update fake /tmp/fake_config.json

sudo -H -u stack tox -e py27integration
retval=$?
set -e

if [ -d ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ ]; then
  cp -r ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ /home/jenkins/workspace/gate-sahara-dashboard-dsvm-integration/
fi
exit $retval
