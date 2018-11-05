"""
I am a self-contained program!
"""

import mitogen


def repr_stuff():
    return repr([__name__, 50])


@mitogen.main()
def main(router):
    context = router.local()
    print(context.call(repr_stuff))
