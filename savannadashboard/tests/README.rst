Savanna Dashboard Selenium Tests
=====================================


Main goal of Selenium Tests
----------

Selenium tests for Savanna Dashboard are designed to check the quality of plug-in Savanna Dashboard for the Horizon.


How to run UI tests:
----------

It's assumed that the savanna and horizon are already installed and running.

Information about installation and start of savanna and horizon can be found on the savanna site
 http://docs.openstack.org/developer/savanna/#user-guide
 in tabs Savanna Installation Guide and Savanna UI Installation Guide.

1. Go to savanna dashboard path.
2. Create config file for selenium tests - `savannadashboard/tests/configs/config.py`.
   You can take a look at the sample config file - `savannadashboard/tests/configs/config.py.sample`.
   All values used in `savannadashboard/tests/configs/parameters.py` file are
   defaults, so, if they are applicable for your environment then you can skip
   config file creation.

3. Install virtual framebuffer X server for X Version 11 (Xvfb):
   sudo apt-get -y install xvfb

4. Install Firefox:
   sudo add-apt-repository ppa:ubuntu-mozilla-security/ppa
   sudo apt-get update
   sudo apt-get install firefox libstdc++5

5. To run ui tests you should use the corresponding tox env: `tox -e tests`.
   If need to run only one test module, use:

   tox -e tests -- -a tags='<module_name>'

   <module_name> may be equal 'cluster', 'cluster_template', 'image_registry', 'node_group_template', 'image_registry', 'vanilla', 'hdp'
   It's full list of actual modules.


Coverage:
----------

-Clusters
-Cluster templates
-Node group templates
-Image registry
-Data sources
-Job binaries
-Jobs
-Job executions