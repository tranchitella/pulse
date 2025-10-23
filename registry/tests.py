from django.test import TestCase

from .models import Device


class DeviceTestCase(TestCase):
    def test_device_str(self):
        device = Device(name="Test Device")
        self.assertEqual(str(device), "Test Device")
