"""
homeassistant.components.sun
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides functionality to keep track of the sun.
"""
import logging
from datetime import timedelta

import homeassistant as ha

STATE_CATEGORY = "weather.sun"

STATE_ABOVE_HORIZON = "above_horizon"
STATE_BELOW_HORIZON = "below_horizon"

STATE_ATTR_NEXT_RISING = "next_rising"
STATE_ATTR_NEXT_SETTING = "next_setting"


def is_up(statemachine):
    """ Returns if the sun is currently up based on the statemachine. """
    return statemachine.is_state(STATE_CATEGORY, STATE_ABOVE_HORIZON)


def next_setting(statemachine):
    """ Returns the datetime object representing the next sun setting. """
    state = statemachine.get_state(STATE_CATEGORY)

    return None if not state else ha.str_to_datetime(
        state['attributes'][STATE_ATTR_NEXT_SETTING])


def next_rising(statemachine):
    """ Returns the datetime object representing the next sun setting. """
    state = statemachine.get_state(STATE_CATEGORY)

    return None if not state else ha.str_to_datetime(
        state['attributes'][STATE_ATTR_NEXT_RISING])


def setup(bus, statemachine, latitude, longitude):
    """ Tracks the state of the sun. """
    logger = logging.getLogger(__name__)

    try:
        import ephem
    except ImportError:
        logger.exception("TrackSun:Error while importing dependency ephem.")
        return False

    sun = ephem.Sun()  # pylint: disable=no-member

    def update_sun_state(now):    # pylint: disable=unused-argument
        """ Method to update the current state of the sun and
            set time of next setting and rising. """
        observer = ephem.Observer()
        observer.lat = latitude
        observer.long = longitude

        next_rising_dt = ephem.localtime(observer.next_rising(sun))
        next_setting_dt = ephem.localtime(observer.next_setting(sun))

        if next_rising_dt > next_setting_dt:
            new_state = STATE_ABOVE_HORIZON
            next_change = next_setting_dt

        else:
            new_state = STATE_BELOW_HORIZON
            next_change = next_rising_dt

        logger.info(
            "Sun:{}. Next change: {}".format(new_state,
                                             next_change.strftime("%H:%M")))

        state_attributes = {
            STATE_ATTR_NEXT_RISING: ha.datetime_to_str(next_rising_dt),
            STATE_ATTR_NEXT_SETTING: ha.datetime_to_str(next_setting_dt)
        }

        statemachine.set_state(STATE_CATEGORY, new_state, state_attributes)

        # +10 seconds to be sure that the change has occured
        ha.track_time_change(bus, update_sun_state,
                             point_in_time=next_change + timedelta(seconds=10))

    update_sun_state(None)

    return True
