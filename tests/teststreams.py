"""
Unit test of the streams system
"""
import param
from holoviews.element.comparison import ComparisonTestCase
from holoviews.streams import * # noqa (Test all available streams)

def test_all_stream_parameters_constant():
    all_stream_cls = [v for v in globals().values() if
                      isinstance(v, type) and issubclass(v, Stream)]
    for stream_cls in all_stream_cls:
        for name, param in stream_cls.params().items():
            if param.constant != True:
                raise TypeError('Parameter %s of stream %s not declared constant'
                                % (name, stream_cls.__name__))

class TestSubscriber(object):

    def __init__(self):
        self.call_count = 0
        self.kwargs = None

    def __call__(self, **kwargs):
        self.call_count += 1
        self.kwargs = kwargs


class TestPositionStreams(ComparisonTestCase):

    def test_positionX_init(self):
        PositionX()

    def test_positionXY_init_contents(self):
        position = PositionXY(x=1, y=3)
        self.assertEqual(position.contents, dict(x=1, y=3))

    def test_positionXY_update_contents(self):
        position = PositionXY()
        position.update(x=5, y=10)
        self.assertEqual(position.contents, dict(x=5, y=10))

    def test_positionY_const_parameter(self):
        position = PositionY()
        try:
            position.y = 5
            raise Exception('No constant parameter exception')
        except TypeError as e:
            self.assertEqual(str(e), "Constant parameter 'y' cannot be modified")


class TestParamValuesStream(ComparisonTestCase):

    def setUp(self):

        class Inner(param.Parameterized):

            x = param.Number(default = 0)
            y = param.Number(default = 0)

        self.inner = Inner

    def tearDown(self):
        self.inner.x = 0
        self.inner.y = 0

    def test_object_contents(self):
        obj = self.inner()
        stream = ParamValues(obj)
        self.assertEqual(stream.contents, {'x':0, 'y':0})

    def test_class_value(self):
        stream = ParamValues(self.inner)
        self.assertEqual(stream.contents, {'x':0, 'y':0})

    def test_object_value_update(self):
        obj = self.inner()
        stream = ParamValues(obj)
        self.assertEqual(stream.contents, {'x':0, 'y':0})
        stream.update(x=5, y=10)
        self.assertEqual(stream.contents, {'x':5, 'y':10})

    def test_class_value_update(self):
        stream = ParamValues(self.inner)
        self.assertEqual(stream.contents, {'x':0, 'y':0})
        stream.update(x=5, y=10)
        self.assertEqual(stream.contents, {'x':5, 'y':10})



class TestSubscribers(ComparisonTestCase):

    def test_exception_subscriber(self):
        subscriber = TestSubscriber()
        position = PositionXY(subscribers=[subscriber])
        kwargs = dict(x=3, y=4)
        position.update(**kwargs)
        self.assertEqual(subscriber.kwargs, kwargs)

    def test_subscriber_disabled(self):
        subscriber = TestSubscriber()
        position = PositionXY(subscribers=[subscriber])
        kwargs = dict(x=3, y=4)
        position.update(trigger=False, **kwargs)
        self.assertEqual(subscriber.kwargs, None)


    def test_subscribers(self):
        subscriber1 = TestSubscriber()
        subscriber2 = TestSubscriber()
        position = PositionXY(subscribers=[subscriber1, subscriber2])
        kwargs = dict(x=3, y=4)
        position.update(**kwargs)
        self.assertEqual(subscriber1.kwargs, kwargs)
        self.assertEqual(subscriber2.kwargs, kwargs)

    def test_batch_subscriber(self):
        subscriber = TestSubscriber()

        positionX = PositionX(subscribers=[subscriber])
        positionY = PositionY(subscribers=[subscriber])

        positionX.update(trigger=False, x=5)
        positionY.update(trigger=False, y=10)

        Stream.trigger([positionX, positionY])
        self.assertEqual(subscriber.kwargs, dict(x=5, y=10))
        self.assertEqual(subscriber.call_count, 1)

    def test_batch_subscribers(self):
        subscriber1 = TestSubscriber()
        subscriber2 = TestSubscriber()

        positionX = PositionX(subscribers=[subscriber1, subscriber2])
        positionY = PositionY(subscribers=[subscriber1, subscriber2])

        positionX.update(trigger=False, x=50)
        positionY.update(trigger=False, y=100)

        Stream.trigger([positionX, positionY])

        self.assertEqual(subscriber1.kwargs, dict(x=50, y=100))
        self.assertEqual(subscriber1.call_count, 1)

        self.assertEqual(subscriber2.kwargs, dict(x=50, y=100))
        self.assertEqual(subscriber2.call_count, 1)


class TestParameterRenaming(ComparisonTestCase):

    def test_simple_rename_constructor(self):
        xy = PositionXY(rename={'x':'xtest', 'y':'ytest'}, x=0, y=4)
        self.assertEqual(xy.contents, {'xtest':0, 'ytest':4})

    def test_invalid_rename_constructor(self):
        with self.assertRaises(KeyError) as cm:
            PositionXY(rename={'x':'xtest', 'z':'ytest'}, x=0, y=4)
            self.assertEqual(str(cm).endswith('is not a stream parameter'), True)

    def test_clashing_rename_constructor(self):
        with self.assertRaises(KeyError) as cm:
            PositionXY(rename={'x':'xtest', 'y':'x'}, x=0, y=4)
            self.assertEqual(str(cm).endswith('parameter of the same name'), True)

    def test_simple_rename_method(self):
        xy = PositionXY(x=0, y=4)
        renamed = xy.rename(x='xtest', y='ytest')
        self.assertEqual(renamed.contents, {'xtest':0, 'ytest':4})

    def test_invalid_rename_method(self):
        xy = PositionXY(x=0, y=4)
        with self.assertRaises(KeyError) as cm:
            renamed = xy.rename(x='xtest', z='ytest')
            self.assertEqual(str(cm).endswith('is not a stream parameter'), True)

    def test_clashing_rename_method(self):
        xy = PositionXY(x=0, y=4)
        with self.assertRaises(KeyError) as cm:
            renamed = xy.rename(x='xtest', y='x')
            self.assertEqual(str(cm).endswith('parameter of the same name'), True)
