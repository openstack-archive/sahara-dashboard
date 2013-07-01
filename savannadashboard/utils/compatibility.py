"""Provide compatibility with various OpenStack releases.

All the code which depends on OpenStack release version should be placed there.
Folsom is the oldest recognizable release.
"""


def get_dashboard_release():
    """Return release codename of currently running Dashboard."""
    import horizon.version

    if hasattr(horizon.version, 'HORIZON_VERSION'):
        return 'folsom'

    return 'grizzly'


def _is_folsom():
    return get_dashboard_release() == 'folsom'


def convert_url(link):
    """Expect grizzly url and convert it to folsom if needed

    For example, 'horizon:project:instances:detail' should be converted to
    'horizon:nova:instances:detail'
    """
    if _is_folsom():
        return link.replace('project', 'nova', 1)
    return link
