OpenStack Dashboard plugin for Sahara project
=============================================

How to use with Horizon on server:
----------------------------------

Use pip to install the package on the server running Horizon. Then either copy
or link the files in sahara_dashboard/enabled to
openstack_dashboard/local/enabled. This step will cause the Horizon service to
pick up the Sahara plugin when it starts.

How to use with devstack:
-------------------------

Add the following to your devstack ``local.conf`` file::

    enable_plugin sahara-dashboard git://git.openstack.org/openstack/sahara-dashboard


To run unit tests:
------------------

./run_tests.sh

NOTE:
=====

As of the Mitaka release, the dashboard for sahara is now maintained
outside of the horzon codebase, in the repository.

Links:
------

Sahara project: https://github.com/openstack/sahara

Sahara at wiki.openstack.org: https://wiki.openstack.org/wiki/Sahara

Launchpad project: https://launchpad.net/sahara

Sahara docs site: http://docs.openstack.org/developer/sahara

Roadmap: https://wiki.openstack.org/wiki/Sahara/Roadmap

Quickstart guide: http://docs.openstack.org/developer/sahara/devref/quickstart.html

How to participate: http://docs.openstack.org/developer/sahara/devref/how_to_participate.html


License
-------

Apache License Version 2.0 http://www.apache.org/licenses/LICENSE-2.0
