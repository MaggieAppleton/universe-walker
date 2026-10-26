"""Share what the screen shows in the pairing advert's scan response.

The native link owns the advertisement itself (flags plus its 24-byte peer
announcement) but never sets a scan response. A laptop scanning actively can
read this status from there without connecting, so pairing is unchanged.
"""

import binascii
import struct
import time

VERSION = 1
# Demo-only 16-bit service-data UUID ("UW"). Service data stays separate from
# the link's manufacturer data when macOS merges advert and scan response.
SERVICE_UUID = 0x5557
FORMAT = "<BB8sBBBIII"
SIZE = struct.calcsize(FORMAT)
NONE = 0xFFFFFFFF
NO_PROGRESS = 255
UNKNOWN_STATUS = 255
FLAG_SUCCESS = 1
MIN_INTERVAL_MS = 500

# Order is the wire format: append new strings, never reorder.
STATUSES = (
    "Hold badges back to back",
    "Hold steady",
    "Syncing...",
    "Synced",
    "Move badges apart",
    "Pull badges apart",
    "Hold together to retry",
    "Could not sync - try again",
    "Sync paused - reopen Walking",
    "Step sensor unavailable",
    "Progress not saved",
)


def _count(value):
    return NONE if value is None else max(0, min(NONE - 1, int(value)))


def pack(device_id, seq, own, team, partner, status, progress=None, success_total=None):
    """Encode one screen state. During success, team carries the synced total."""
    flags = 0
    if success_total is not None:
        flags |= FLAG_SUCCESS
        team = success_total
    code = STATUSES.index(status) if status in STATUSES else UNKNOWN_STATUS
    hold = NO_PROGRESS if progress is None else max(0, min(254, int(progress * 200 + 0.5)))
    return struct.pack(FORMAT, VERSION, seq & 255, binascii.unhexlify(device_id), code, hold, flags,
                       _count(own), _count(team), _count(partner))


def unpack(data):
    """Decode a payload, or return None when it is not this version/shape."""
    if len(data) < SIZE or data[0] != VERSION:
        return None
    _, seq, raw_id, code, hold, flags, own, team, partner = struct.unpack(FORMAT, bytes(data[:SIZE]))
    return {
        "id": binascii.hexlify(raw_id).decode(),
        "seq": seq,
        "status": STATUSES[code] if code < len(STATUSES) else None,
        "progress": None if hold == NO_PROGRESS else hold / 200,
        "success": bool(flags & FLAG_SUCCESS),
        "own": own,
        "team": None if team == NONE else team,
        "partner": None if partner == NONE else partner,
    }


def scan_response(payload):
    return bytes((len(payload) + 3, 0x16, SERVICE_UUID & 255, SERVICE_UUID >> 8)) + payload


class Beacon:
    """Adds the status to whatever the native link advertises.

    Only re-advertises while the link is idle and already advertising, so it
    never starts advertising on its own or during a badge-to-badge session.
    """

    def __init__(self, radio, link, device_id):
        self.radio = radio
        self.link = link
        self.device_id = device_id
        self._advertise = radio.advertise
        self._stop = radio.stop_advertise
        self.call = None
        self.response = None
        self.payload = None
        self.seq = 0
        self.sent_at = None
        self.last_send = None
        radio.advertise = self._link_advertise
        radio.stop_advertise = self._link_stop

    def _send(self, args, kwargs):
        if self.response is not None:
            kwargs = dict(kwargs)
            kwargs["resp_data"] = self.response
        return self._advertise(*args, **kwargs)

    def _link_advertise(self, *args, **kwargs):
        self.call = (args, kwargs)
        self.sent_at = self.seq
        return self._send(args, kwargs)

    def _link_stop(self, *args, **kwargs):
        self.call = None
        return self._stop(*args, **kwargs)

    def _idle(self):
        # radio.in_session stays True for the whole idle Link, so it is not a signal.
        link = self.link
        return link is not None and not (link.linked or getattr(link, "linking", False)
                                         or getattr(self.radio, "connections", None))

    def publish(self, own, team, partner, status, progress=None, success_total=None):
        state = (own, team, partner, status, progress, success_total)
        if state != self.payload:
            self.payload = state
            self.seq += 1
            self.response = scan_response(pack(self.device_id, self.seq, *state))
            self.sent_at = None
        if self.call is None or self.sent_at == self.seq or not self._idle():
            return
        now = time.ticks_ms()
        if self.last_send is not None and time.ticks_diff(now, self.last_send) < MIN_INTERVAL_MS:
            return
        self.last_send = now
        self.sent_at = self.seq
        self._send(*self.call)

    def close(self):
        self.radio.advertise = self._advertise
        self.radio.stop_advertise = self._stop
