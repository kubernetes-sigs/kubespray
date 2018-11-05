
import logging
import mitogen.master

def foo():
    pass

logging.basicConfig(level=logging.INFO)
router = mitogen.master.Router()

l = router.local()
l.call(foo)
