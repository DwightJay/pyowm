from pyowm.constants import ALERT_API_VERSION
from pyowm.commons.http_client import HttpClient
from pyowm.alertapi30.parsers import TriggerParser
from pyowm.alertapi30.uris import TRIGGERS_URI, NAMED_TRIGGER_URI
from pyowm.utils import timeformatutils
from pyowm.utils import stringutils


class AlertManager:

    """
    A manager objects that provides a full interface to OWM Alert API. It implements CRUD methods on Trigger entities
    and read/deletion of related Alert objects

    :param API_key: the OWM web API key
    :type API_key: str
    :returns: an *AlertManager* instance
    :raises: *AssertionError* when no API Key is provided

    """

    def __init__(self, API_key):
        assert API_key is not None, 'You must provide a valid API Key'
        self.API_key = API_key
        self.trigger_parser = TriggerParser()
        self.http_client = HttpClient()

    def alert_api_version(self):
        return ALERT_API_VERSION

    # TRIGGER methods

    def create_trigger(self,  start, end, conditions, area, alert_channels=None):
        """
        Create a new trigger on the Alert API with the given parameters
        :param start: time object representing the time when the trigger begins to be checked
        :type start: int, ``datetime.datetime`` or ISO8601-formatted string
        :param end: time object representing the time when the trigger ends to be checked
        :type end: int, ``datetime.datetime`` or ISO8601-formatted string
        :param conditions: the `Condition` objects representing the set of checks to be done on weather variables
        :type conditions: list of `pyowm.utils.alertapi30.Condition` instances
        :param area: the geographic are over which conditions are checked: it can be composed by multiple geoJSON types
        :type area: list of geoJSON types (str)
        :param alert_channels: the alert channels through which alerts originating from this `Trigger` can be consumed.
        Defaults to OWM API polling
        :type alert_channels: list of `pyowm.utils.alertapi30.AlertChannel` instances
        :returns:  a *Trigger* instance
        :raises: *ValueError* when start or end epochs are `None` or when end precedes start or when conditions or area
        are empty collections
        """
        assert start is not None
        assert end is not None
        unix_start = timeformatutils.to_UNIXtime(start)
        unix_end = timeformatutils.to_UNIXtime(end)
        if unix_start >= unix_end:
            raise ValueError("Error: the start epoch must precede the end epoch")
        the_time_period = {
            "start": {
                "expression": "exact",
                "amount": unix_start
            },
            "end": {
                "expression": "exact",
                "amount": unix_end
            }
        }

        assert conditions is not None
        if len(conditions) == 0:
            raise ValueError('A trigger must contain at least one condition: you provided none')
        the_conditions = [dict(name=c.weather_param, expression=c.operator, amount=c.amount) for c in conditions]

        assert area is not None
        if len(area) == 0:
            raise ValueError('The area for a trigger must contain at least one geoJSON type: you provided none')
        the_area = [a.geojson() for a in area]

        # >>> for the moment, no specific handling for alert channels

        status, payload = self.http_client.post(
            TRIGGERS_URI,
            params={'appid': self.API_key},
            data=dict(time_period=the_time_period, conditions=the_conditions, area=the_area),
            headers={'Content-Type': 'application/json'})
        return self.trigger_parser.parse_dict(payload)

    def get_triggers(self):
        """
        Retrieves all of the user's triggers that are set on the Weather Alert API.

        :returns: list of `pyowm.alertapi30.trigger.Trigger` objects

        """
        status, data = self.http_client.get_json(
            TRIGGERS_URI,
            params={'appid': self.API_key},
            headers={'Content-Type': 'application/json'})
        return [self.trigger_parser.parse_dict(item) for item in data]

    def get_trigger(self, trigger_id):
        """
        Retrieves the named trigger from the Weather Alert API.

        :param trigger_id: the ID of the trigger
        :type trigger_id: str
        :return: a `pyowm.alertapi30.trigger.Trigger` instance
        """
        stringutils.assert_is_string_or_unicode(trigger_id)
        status, data = self.http_client.get_json(
            NAMED_TRIGGER_URI % trigger_id,
            params={'appid': self.API_key},
            headers={'Content-Type': 'application/json'})
        return self.trigger_parser.parse_dict(data)

    def update_trigger(self, trigger):
        """
        Updates on the Alert API the trigger record having the ID of the specified Trigger object: the remote record is
        updated with data from the local Trigger object.

        :param trigger: the Trigger with updated data
        :type trigger: `pyowm.alertapi30.trigger.Trigger`
        :return: ``None``
        """
        assert trigger is not None
        stringutils.assert_is_string_or_unicode(trigger.id)
        the_time_period = {
            "start": {
                "expression": "exact",
                "amount": trigger.start
            },
            "end": {
                "expression": "exact",
                "amount": trigger.end
            }
        }
        the_conditions = [dict(name=c.weather_param, expression=c.operator, amount=c.amount) for c in trigger.conditions]
        the_area = [a.geojson() for a in trigger.area]

        status, _ = self.http_client.put(
            NAMED_TRIGGER_URI % trigger.id,
            params={'appid': self.API_key},
            data=dict(time_period=the_time_period, conditions=the_conditions, area=the_area),
            headers={'Content-Type': 'application/json'})

    def delete_trigger(self, trigger):
        """
        Deletes from the Alert API the trigger record identified by the ID of the provided
        `pyowm.alertapi30.trigger.Trigger`, along with all related alerts

        :param trigger: the `pyowm.alertapi30.trigger.Trigger` object to be deleted
        :type trigger: `pyowm.alertapi30.trigger.Trigger`
        :returns: `None` if deletion is successful, an exception otherwise
        """
        assert trigger is not None
        stringutils.assert_is_string_or_unicode(trigger.id)
        status, _ = self.http_client.delete(
            NAMED_TRIGGER_URI % str(trigger.id),
            params={'appid': self.API_key},
            headers={'Content-Type': 'application/json'})

    # ALERTS methods

    def get_alerts_for(self, trigger):
        raise NotImplementedError()

    def get_alert(self, alert_id):
        raise NotImplementedError()

    def delete_all_alerts_for(self, trigger):
        raise NotImplementedError()

    def delete_alert(self, alert):
        raise NotImplementedError()

