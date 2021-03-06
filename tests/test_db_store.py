import contextlib
import datetime
import os
import shutil
import sqlite3
import tempfile
import unittest

import mock
from dateutil import tz
import pytz

from greenpithumb import db_store

# Timezone offset info for EST (UTC minus 5 hours).
UTC_MINUS_5 = tz.tzoffset(None, -18000)


class OpenOrCreateTest(unittest.TestCase):

    def setUp(self):
        self._temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self._temp_dir)

    @mock.patch.object(sqlite3, 'connect')
    def test_does_not_initialize_existing_db_file(self, mock_connect):
        mock_connection = mock.Mock()
        mock_connect.return_value = mock_connection
        # Simulate an existing database file
        with tempfile.NamedTemporaryFile() as temp_file:
            with contextlib.closing(db_store.open_or_create_db(temp_file.name)):
                mock_connect.assert_called_once_with(temp_file.name)
        # If the database already existed, we should not do anything except
        # call sqlite3.connect().
        mock_connection.cursor.assert_not_called()
        mock_connection.commit.assert_not_called()

    def test_creates_file_and_tables_when_db_does_not_already_exist(self):
        # Create a path for a file that does not already exist.
        db_path = os.path.join(self._temp_dir, 'test.db')
        with contextlib.closing(db_store.open_or_create_db(
                db_path)) as connection:
            cursor = connection.cursor()
            # Insertions into all tables should work after initialization.
            cursor.execute('INSERT INTO temperature VALUES (?, ?)',
                           ('2016-07-23T10:51Z', 98.6))
            cursor.execute('INSERT INTO humidity VALUES (?, ?)',
                           ('2016-07-23T10:51Z', 93.7))
            cursor.execute('INSERT INTO soil_moisture VALUES (?, ?)',
                           ('2016-07-23T10:51Z', 57))
            cursor.execute('INSERT INTO light VALUES (?, ?)',
                           ('2016-07-23T10:51Z', 75.2))
            cursor.execute('INSERT INTO watering_events VALUES (?, ?)',
                           ('2016-07-23T10:51Z', 258.9))
            connection.commit()


class StoreClassesTest(unittest.TestCase):

    def setUp(self):
        self.mock_cursor = mock.Mock()
        self.mock_connection = mock.Mock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    def test_insert_soil_moisture(self):
        """Should insert timestamp and moisture level into database."""
        record = db_store.SoilMoistureRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc),
            soil_moisture=300)
        store = db_store.SoilMoistureStore(self.mock_connection)
        store.insert(record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO soil_moisture VALUES (?, ?)', ('2016-07-23T10:51Z',
                                                        300))
        self.mock_connection.commit.assert_called_once()

    def test_insert_soil_moisture_with_non_utc_time(self):
        """Should insert timestamp and moisture level into database."""
        record = db_store.SoilMoistureRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=UTC_MINUS_5),
            soil_moisture=300)
        store = db_store.SoilMoistureStore(self.mock_connection)
        store.insert(record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO soil_moisture VALUES (?, ?)', ('2016-07-23T15:51Z',
                                                        300))
        self.mock_connection.commit.assert_called_once()

    def test_get_soil_moisture(self):
        store = db_store.SoilMoistureStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = [('2016-07-23T10:51Z', 300),
                                                  ('2016-07-23T10:52Z', 400)]
        soil_moisture_data = store.get()
        soil_moisture_data.sort(
            key=lambda SoilMoistureRecord: SoilMoistureRecord.timestamp)

        self.assertEqual(
            soil_moisture_data[0].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc))
        self.assertEqual(soil_moisture_data[0].soil_moisture, 300)
        self.assertEqual(
            soil_moisture_data[1].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 52, 0, tzinfo=pytz.utc))
        self.assertEqual(soil_moisture_data[1].soil_moisture, 400)

    def test_get_soil_moisture_empty_database(self):
        store = db_store.SoilMoistureStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = []
        soil_moisture_data = store.get()
        self.assertEqual(soil_moisture_data, [])

    def test_insert_light(self):
        """Should insert timestamp and light into database."""
        light_record = db_store.LightRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc),
            light=50.0)
        store = db_store.LightStore(self.mock_connection)
        store.insert(light_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO light VALUES (?, ?)', ('2016-07-23T10:51Z', 50.0))
        self.mock_connection.commit.assert_called_once()

    def test_insert_light_with_non_utc_time(self):
        """Should insert timestamp and light into database."""
        light_record = db_store.LightRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=UTC_MINUS_5),
            light=50.0)
        store = db_store.LightStore(self.mock_connection)
        store.insert(light_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO light VALUES (?, ?)', ('2016-07-23T15:51Z', 50.0))
        self.mock_connection.commit.assert_called_once()

    def test_get_light(self):
        store = db_store.LightStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = [('2016-07-23T10:51Z', 300),
                                                  ('2016-07-23T10:52Z', 400)]
        light_data = store.get()
        light_data.sort(key=lambda LightRecord: LightRecord.timestamp)

        self.assertEqual(
            light_data[0].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc))
        self.assertEqual(light_data[0].light, 300)
        self.assertEqual(
            light_data[1].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 52, 0, tzinfo=pytz.utc))
        self.assertEqual(light_data[1].light, 400)

    def test_get_light_empty_database(self):
        store = db_store.LightStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = []
        light_data = store.get()
        self.assertEqual(light_data, [])

    def test_insert_humidity(self):
        """Should insert timestamp and humidity level into database."""
        humidity_record = db_store.HumidityRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc),
            humidity=50.0)
        store = db_store.HumidityStore(self.mock_connection)
        store.insert(humidity_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO humidity VALUES (?, ?)', ('2016-07-23T10:51Z', 50.0))
        self.mock_connection.commit.assert_called_once()

    def test_insert_humidity_with_non_utc_time(self):
        """Should insert timestamp and humidity level into database."""
        humidity_record = db_store.HumidityRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=UTC_MINUS_5),
            humidity=50.0)
        store = db_store.HumidityStore(self.mock_connection)
        store.insert(humidity_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO humidity VALUES (?, ?)', ('2016-07-23T15:51Z', 50.0))
        self.mock_connection.commit.assert_called_once()

    def test_get_humidity(self):
        store = db_store.HumidityStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = [('2016-07-23T10:51Z', 50),
                                                  ('2016-07-23T10:52Z', 51)]
        humidity_data = store.get()
        humidity_data.sort(key=lambda HumidityRecord: HumidityRecord.timestamp)

        self.assertEqual(
            humidity_data[0].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc))
        self.assertEqual(humidity_data[0].humidity, 50)
        self.assertEqual(
            humidity_data[1].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 52, 0, tzinfo=pytz.utc))
        self.assertEqual(humidity_data[1].humidity, 51)

    def test_get_humidity_empty_database(self):
        store = db_store.HumidityStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = []
        humidity_data = store.get()
        self.assertEqual(humidity_data, [])

    def test_insert_temperature(self):
        """Should insert timestamp and temperature into database."""
        temperature_record = db_store.TemperatureRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc),
            temperature=21.1)
        store = db_store.TemperatureStore(self.mock_connection)
        store.insert(temperature_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO temperature VALUES (?, ?)',
            ('2016-07-23T10:51Z', 21.1))
        self.mock_connection.commit.assert_called_once()

    def test_insert_temperature_with_non_utc_time(self):
        """Should insert timestamp and temperature into database."""
        temperature_record = db_store.TemperatureRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=UTC_MINUS_5),
            temperature=21.1)
        store = db_store.TemperatureStore(self.mock_connection)
        store.insert(temperature_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO temperature VALUES (?, ?)',
            ('2016-07-23T15:51Z', 21.1))
        self.mock_connection.commit.assert_called_once()

    def test_get_temperature(self):
        store = db_store.TemperatureStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = [('2016-07-23T10:51Z', 21.0),
                                                  ('2016-07-23T10:52Z', 21.5)]
        temperature_data = store.get()
        temperature_data.sort(
            key=lambda TemperatureRecord: TemperatureRecord.timestamp)

        self.assertEqual(
            temperature_data[0].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc))
        self.assertEqual(temperature_data[0].temperature, 21.0)
        self.assertEqual(
            temperature_data[1].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 52, 0, tzinfo=pytz.utc))
        self.assertEqual(temperature_data[1].temperature, 21.5)

    def test_get_temperature_empty_database(self):
        store = db_store.TemperatureStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = []
        temperature_data = store.get()
        self.assertEqual(temperature_data, [])

    def test_insert_water_pumped(self):
        """Should insert timestamp and volume of water pumped into database."""
        watering_event_record = db_store.WateringEventRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc),
            water_pumped=200.0)
        store = db_store.WateringEventStore(self.mock_connection)
        store.insert(watering_event_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO watering_events VALUES (?, ?)', ('2016-07-23T10:51Z',
                                                          200.0))
        self.mock_connection.commit.assert_called_once()

    def test_insert_water_pumped_with_non_utc_time(self):
        """Should insert timestamp and volume of water pumped into database."""
        watering_event_record = db_store.WateringEventRecord(
            timestamp=datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=UTC_MINUS_5),
            water_pumped=200.0)
        store = db_store.WateringEventStore(self.mock_connection)
        store.insert(watering_event_record)
        self.mock_cursor.execute.assert_called_once_with(
            'INSERT INTO watering_events VALUES (?, ?)', ('2016-07-23T15:51Z',
                                                          200.0))
        self.mock_connection.commit.assert_called_once()

    def test_get_water_pumped(self):
        store = db_store.WateringEventStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = [('2016-07-23T10:51Z', 300),
                                                  ('2016-07-23T10:52Z', 301)]
        watering_event_data = store.get()
        watering_event_data.sort(
            key=lambda WaterintEventRecord: WaterintEventRecord.timestamp)

        self.assertEqual(
            watering_event_data[0].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 51, 0, tzinfo=pytz.utc))
        self.assertEqual(watering_event_data[0].water_pumped, 300)
        self.assertEqual(
            watering_event_data[1].timestamp,
            datetime.datetime(
                2016, 7, 23, 10, 52, 0, tzinfo=pytz.utc))
        self.assertEqual(watering_event_data[1].water_pumped, 301)

    def test_get_water_pumped_empty_database(self):
        store = db_store.WateringEventStore(self.mock_connection)
        self.mock_cursor.fetchall.return_value = []
        watering_event_data = store.get()
        self.assertEqual(watering_event_data, [])
