import unittest
import json
from pyowm.alertapi30.alert_manager import AlertManager
from pyowm.alertapi30.trigger import Trigger
from pyowm.alertapi30.condition import Condition
from pyowm.alertapi30.parsers import TriggerParser
from pyowm.commons.http_client import HttpClient
from pyowm.utils import geo
from pyowm.constants import ALERT_API_VERSION


class MockHttpClient(HttpClient):

    # 1 trigger
    test_trigger_json = '''{"_id":"5852816a9aaacb00153134a3","__v":0,"alerts":
    {"8b48b2cd21c23d2894466caccba1ed1f":{"conditions":[{"current_value":{"min":263.576,"max":263.576},"condition":
    {"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}}],"last_update":1481802090232,
    "date":1482181200000,"coordinates":{"lon":37,"lat":53}}},"area":[{"type":"Point","_id":"5852816a9aaacb00153134a4",
    "coordinates":[37,53]}],"conditions":[{"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}],
    "time_period":{"end":{"amount":432000000,"expression":"exact"},"start":{"amount":132000000,"expression":"exact"}}}'''

    def get_json(self, uri, params=None, headers=None):
        return 200, [json.loads(self.test_trigger_json)]

    def post(self, uri, params=None, data=None, headers=None):
        return 200, json.loads(self.test_trigger_json)

    def put(self, uri, params=None, data=None, headers=None):
        return 200, None

    def delete(self, uri, params=None, data=None, headers=None):
        return 204, None


class MockHttpClientTwoTriggers(HttpClient):
    # 2 triggers
    test_triggers_json = '''[ {"_id":"585280edbe54110025ea52bb","__v":0,"alerts":{},"area":[{"type":"Point",
    "_id":"585280edbe54110025ea52bc","coordinates":[53,37]}],"conditions":[{"name":"temp","expression":"$lt",
    "amount":273,"_id":"585280edbe54110025ea52bd"}],"time_period":{"end":{"amount":432000000,"expression":"exact"},
    "start":{"amount":132000000,"expression":"exact"}}},{"_id":"5852816a9aaacb00153134a3","__v":0,"alerts":
    {"8b48b2cd21c23d2894466caccba1ed1f":{"conditions":[{"current_value":{"min":263.576,"max":263.576},"condition":
    {"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}}],"last_update":1481802090232,
    "date":1482181200000,"coordinates":{"lon":37,"lat":53}}},"area":[{"type":"Point","_id":"5852816a9aaacb00153134a4",
    "coordinates":[37,53]}],"conditions":[{"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}],
    "time_period":{"end":{"amount":432000000,"expression":"exact"},"start":{"amount":132000000,"expression":"exact"}}}]'''

    def get_json(self, uri, params=None, headers=None):
        return 200, json.loads(self.test_triggers_json)


class MockHttpClientOneTrigger(HttpClient):
    # 1 trigger
    test_trigger_json = '''{"_id":"5852816a9aaacb00153134a3","__v":0,"alerts":
    {"8b48b2cd21c23d2894466caccba1ed1f":{"conditions":[{"current_value":{"min":263.576,"max":263.576},"condition":
    {"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}}],"last_update":1481802090232,
    "date":1482181200000,"coordinates":{"lon":37,"lat":53}}},"area":[{"type":"Point","_id":"5852816a9aaacb00153134a4",
    "coordinates":[37,53]}],"conditions":[{"name":"temp","expression":"$lt","amount":273,"_id":"5852816a9aaacb00153134a5"}],
    "time_period":{"end":{"amount":432000000,"expression":"exact"},"start":{"amount":132000000,"expression":"exact"}}}'''

    def get_json(self, uri, params=None, headers=None):
        return 200, json.loads(self.test_trigger_json)


class TestAlertManager(unittest.TestCase):
    _cond1 = Condition('humidity', 'LESS_THAN', 10)
    _cond2 = Condition('temp', 'GREATER_THAN_EQUAL', 100.6)
    _trigger = Trigger(1526809375, 1527809375, [_cond1, _cond2],
                       [geo.Point(13.6, 46.9)], alerts=[], alert_channels=None, id='trigger-id')

    def factory(self, _kls):
        sm = AlertManager('APIKey')
        sm.http_client = _kls()
        return sm

    def test_instantiation_fails_without_api_key(self):
        self.assertRaises(AssertionError, AlertManager, None)

    def test_get_alert_api_version(self):
        instance = AlertManager('APIKey')
        result = instance.alert_api_version()
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ALERT_API_VERSION)

    def test_get_triggers(self):
        instance = self.factory(MockHttpClientTwoTriggers)
        results = instance.get_triggers()
        self.assertEqual(2, len(results))
        t = results[0]
        self.assertIsInstance(t, Trigger)

    def test_get_trigger_fails_with_wrong_input(self):
        instance = AlertManager('APIKey')
        with self.assertRaises(AssertionError):
            instance.get_trigger(None)
        with self.assertRaises(AssertionError):
            instance.get_trigger(123)

    def test_get_trigger(self):
        instance = self.factory(MockHttpClientOneTrigger)
        result = instance.get_trigger('any-id')
        self.assertIsInstance(result, Trigger)

    def test_create_trigger(self):
        instance = self.factory(MockHttpClient)
        result = instance.create_trigger(1526809375, 1527809375, [self._cond1, self._cond2], [geo.Point(13.6, 46.9)], alert_channels=None)
        self.assertIsInstance(result, Trigger)

    def test_create_trigger_fails_with_wrong_inputs(self):
        instance = self.factory(MockHttpClient)
        with self.assertRaises(AssertionError):
            instance.create_trigger(None, 1527809375, [self._cond1, self._cond2], [geo.Point(13.6, 46.9)], alert_channels=None)
        with self.assertRaises(AssertionError):
            instance.create_trigger(1526809375, None, [self._cond1, self._cond2], [geo.Point(13.6, 46.9)], alert_channels=None)
        with self.assertRaises(ValueError):
            instance.create_trigger(1526809375, 1327809375, [self._cond1, self._cond2], [geo.Point(13.6, 46.9)], alert_channels=None)
        with self.assertRaises(AssertionError):
            instance.create_trigger(1526809375, 1527809375, None, [geo.Point(13.6, 46.9)], alert_channels=None)
        with self.assertRaises(ValueError):
            instance.create_trigger(1526809375, 1527809375, [], [geo.Point(13.6, 46.9)], alert_channels=None)
        with self.assertRaises(AssertionError):
            instance.create_trigger(1526809375, 1527809375, [self._cond1, self._cond2], None, alert_channels=None)
        with self.assertRaises(ValueError):
            instance.create_trigger(1526809375, 1527809375, [self._cond1, self._cond2], [], alert_channels=None)

    def test_delete_trigger_fails_with_wrong_input(self):
        instance = AlertManager('APIKey')
        with self.assertRaises(AssertionError):
            instance.delete_trigger(None)
        with self.assertRaises(AssertionError):
            self._trigger.id = 123
            instance.delete_trigger(self._trigger)

    def test_delete_trigger(self):
        instance = self.factory(MockHttpClient)
        parser = TriggerParser()
        trigger = parser.parse_JSON(MockHttpClient.test_trigger_json)
        result = instance.delete_trigger(trigger)
        self.assertIsNone(result)

    def test_update_trigger_fails_with_wrong_input(self):
        instance = AlertManager('APIKey')
        with self.assertRaises(AssertionError):
            instance.update_trigger(None)
        with self.assertRaises(AssertionError):
            self._trigger.id = 123
            instance.update_trigger(self._trigger)

    def test_update_trigger(self):
        instance = self.factory(MockHttpClient)
        parser = TriggerParser()
        modified_trigger = parser.parse_JSON(MockHttpClient.test_trigger_json)
        modified_trigger.id = '5852816a9aaacb00153134a3'
        modified_trigger.end = self._trigger.end + 10000
        result = instance.update_trigger(modified_trigger)
        self.assertIsNone(result)
