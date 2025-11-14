import pytest
from netaddr.core import Publisher, Subscriber
import pprint


class Subject(Publisher):
    pass


class Observer(Subscriber):
    def __init__(self, id):
        self.id = id

    def update(self, data):
        return repr(self), pprint.pformat(data)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.id)


def test_pubsub():
    s = Subject()
    s.attach(Observer('foo'))
    s.attach(Observer('bar'))

    data = [
        {'foo': 42},
        {'list': [1, '2', list(range(10))]},
        {'strings': ['foo', 'bar', 'baz', 'quux']},
    ]
    s.notify(data)

    s.notify(['foo', 'bar', 'baz'])

    with pytest.raises(TypeError):
        s.attach('foo')
