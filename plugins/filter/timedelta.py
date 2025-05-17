from datetime import timedelta


def _timedelta(kwargs):
    return timedelta(**kwargs)


class FilterModule(object):
    """Kubespray utility jinja2 filters"""

    def filters(self):
        return {
            "timedelta": _timedelta,
        }
