import asyncio
import os
from threading import Lock, Thread
import time
from typing import Callable
import pynetbox
from misc import logger

max_netbox_fetch_time = 60 * 5


class DataLoader(Thread):
    def __init__(self, loop: asyncio.AbstractEventLoop, *args, on_reload: Callable | None = None, on_error: Callable | None = None, **kwargs) -> None:
        super().__init__(*args, daemon=True, **kwargs)
        self.loop = loop
        self.on_reload = on_reload
        self.on_error = on_error
        self.is_initialized = False
        self.needs_reload = True
        self.lock = Lock()
        self.intermediate_data = {
            'interfaces': [],
            'devices': [],
            'ip_addresses': [],
            'tags': [],
            'locations': [],
            'power_ports': []
        }
        self._data = {
            'devices': [],
            'tags': [],
            'locations': []
        }
        self._is_fetching = False
        self._start_fetch_time = time.time()
        self._end_fetch_time = time.time()

    async def __aenter__(self):
        while not self.is_initialized:
            await asyncio.sleep(1)
        return self

    async def __aexit__(self, *_):
        pass

    @property
    def devices(self):
        self.lock.acquire()
        result = self._data['devices']
        self.lock.release()
        return result

    @property
    def tags(self):
        self.lock.acquire()
        result = self._data['tags']
        self.lock.release()
        return result

    @property
    def locations(self):
        self.lock.acquire()
        result = self._data['locations']
        self.lock.release()
        return result

    def reload(self):
        self.needs_reload = True

    def _watchdog(self):
        while True:
            if self._is_fetching and (time.time() - self._start_fetch_time) > max_netbox_fetch_time:
                logger.error('DataLoader fetch took too long.')
                if self.on_error:
                    self.on_error()
            time.sleep(1)

    def run(self):
        apiToken = os.getenv('NETBOX_API_TOKEN')
        nb = pynetbox.api(os.getenv('NETBOX_API_URL'),
                          token=apiToken,
                          threading=True)
        nb.http_session.verify = False
        try:
            nb.openapi()
        except Exception as e:
            logger.exception(e)
            if self.on_error:
                self.on_error()
                return

        self._watchdog_thread = Thread(target=self._watchdog, daemon=True)
        self._watchdog_thread.start()

        while True:
            if self.needs_reload or not self.is_initialized:
                self._is_fetching = True
                self._start_fetch_time = time.time()
                self.intermediate_data['interfaces'] = [
                    dict(interface) for interface in nb.dcim.interfaces.all()]
                self.intermediate_data['ip_addresses'] = [
                    dict(ip_address) for ip_address in nb.ipam.ip_addresses.all()]
                self.intermediate_data['tags'] = [dict(tag)
                                                  for tag in nb.extras.tags.all()]
                self.intermediate_data['locations'] = [
                    dict(location) for location in nb.dcim.locations.all()]
                self.intermediate_data['power_ports'] = list(
                    nb.dcim.power_ports.all())
                self.intermediate_data['devices'] = self._get_devices(
                    [device for device in nb.dcim.devices.all()
                     if device.primary_ip is not None
                     and device['status']['value'] == 'active'])
                self._is_fetching = False
                self.lock.acquire()
                self._data['devices'] = self.intermediate_data['devices'].copy()
                self._data['tags'] = self.intermediate_data['tags'].copy()
                self._data['locations'] = self.intermediate_data['locations'].copy()
                self.lock.release()
                if self.on_reload:
                    asyncio.run_coroutine_threadsafe(
                        self.on_reload(), self.loop)
                self.is_initialized = True
                self.needs_reload = False
            else:
                time.sleep(60)

    def _get_devices(self, rawDevices) -> list:
        devices = [
            {
                **dict(device),
                'interfaces': [dict(interface) for interface in self.intermediate_data['interfaces'] if interface['device']['id'] == device['id']],
            } for device in rawDevices
        ]
        for i, device in enumerate(devices):
            ip_address = [
                ip_address for ip_address in self.intermediate_data['ip_addresses'] if ip_address['id'] == device['primary_ip']['id']][0]
            dev_power_ports = [
                power_port for power_port in self.intermediate_data['power_ports'] if power_port['device']['id'] == device['id']]
            [[peer.full_details() for peer in p.link_peers]
                for p in dev_power_ports]
            devices[i]['power_ports'] = [
                dict(port) for port in dev_power_ports]
            devices[i]['primary_ip'] = dict(ip_address)
            devices[i]['tags'] = ip_address['tags']

        devices = [device for device in devices
                   if device['status']['value'] == 'active']
        return devices
