#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

set -ex
source commons $@

cd /opt/stack/new/sahara-dashboard
sudo -H -u stack tox -e py27integration
retval=$?
if [ -d ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ ]; then
  cp -r ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ /home/jenkins/workspace/gate-sahara-dashboard-dsvm-integration/
fi
exit $retval
