README for resources
=====================================

Resources in this directory using for check EDP for Sahara.
For this purpose the cluster with oozie by process is created.
With these resources created and launched jobs.
Success of performance of jobs is checked.

Pig job
-------------------------------------

Description.
------------

Resources 'edp-job.pig' and 'edp-lib.jar' used for create oozie job
that deletes all symbols in line after ":".

Example:
--------

input file:
"""
qweqwe
qweqweqwe:
qweqweqwe:qwe
:ertertert
asd
"""

output file:
"""
qweqwe
qweqweqwe
asd
"""

Sources.
--------

Link for 'edp-job.pig':
https://github.com/apache/oozie/blob/branch-4.0/examples/src/main/apps/pig/id.pig

Source for 'edp-lib.jar':
https://github.com/apache/oozie/blob/branch-4.0/examples/src/main/java/org/apache/oozie/example/DateList.java


MapReduce job
-------------------------------------

Description.
------------

Resource 'edp-job.jar' used for create oozie job
which counts the characters in file and displays values ​​at end of each line.

Example:
--------

input file:
"""
qweqwe
qweqweqwe:
qweqweqwe:qwe
:ertertert
asd
"""

output file:
"""
qweqwe 6
qweqweqwe: 16
qweqweqwe:qwe 29
:ertertert 39
asd 42
"""

Sources.
--------

Sources for 'edp-job.jar':
https://github.com/apache/oozie/blob/branch-4.0/examples/src/main/java/org/apache/oozie/example/SampleMapper.java
https://github.com/apache/oozie/blob/branch-4.0/examples/src/main/java/org/apache/oozie/example/SampleReducer.java