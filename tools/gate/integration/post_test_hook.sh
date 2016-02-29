#!/bin/bash

# This script will be executed inside post_test_hook function in devstack gate

set -x
source commons $@

set +e
cd /opt/stack/new/sahara-dashboard
sudo -H -u stack tox -e py27integration
retval=$?
set -e

if [ -d ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ ]; then
  cp -r ${SAHARA_DASHBOARD_SCREENSHOTS_DIR}/ /home/jenkins/workspace/gate-sahara-dashboard-dsvm-integration/
fi
exit $retval
