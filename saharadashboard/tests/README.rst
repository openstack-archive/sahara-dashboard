Sahara Dashboard Selenium Tests
=====================================


Main goal of Selenium Tests
----------

Selenium tests for Sahara Dashboard are designed to check the correctness of the Sahara Dashboard Horizon plug-in.


How to run UI tests:
----------

It's assumed that sahara and horizon are already installed and running.

Information about installation and start of sahara and horizon can be found on the sahara site
 http://docs.openstack.org/developer/sahara/#user-guide
 in tabs Sahara Installation Guide and Sahara UI Installation Guide.

1. Go to sahara dashboard path.
2. Create config file for selenium tests - `saharadashboard/tests/configs/config.py`.
   You can take a look at the sample config file - `saharadashboard/tests/configs/config.py.sample`.
   All values used in `saharadashboard/tests/configs/parameters.py` file are
   defaults, so, if they are applicable for your environment then you can skip
   config file creation.

3. Install virtual framebuffer X server for X Version 11 (Xvfb):
   sudo apt-get -y install xvfb

4. Install Firefox:
   sudo add-apt-repository ppa:ubuntu-mozilla-security/ppa
   sudo apt-get update
   sudo apt-get install firefox libstdc++5

5. To run ui tests you should use the corresponding tox env: `tox -e uitests`.
   If need to run only one test module, use:

   tox -e uitests -- '<module_name>'

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
