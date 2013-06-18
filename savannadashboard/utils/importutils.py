from savannadashboard.openstack.common import importutils


def import_any(*args):
    for module_name in args:
        module = importutils.try_import(module_name)
        if module is not None:
            return module

    raise RuntimeError('Unable to import any modules from the list %s' %
                       args)
