"""Use the stock badge-link pairing flow for one brief step exchange."""

from badgeware import link as badgelink
from pairing_trace import PairingTrace
from sync_protocol import Exchange, PACKET_SIZE

# Merge Conflict's initial greeting is 94 bytes. Its send queue naturally
# waits past the initial 19-byte capacity while the connection is being set
# up. Use the same threshold before starting our smaller step exchange.
START_CAPACITY = 94


class BadgeSync:
    # All timestamps come from badge.ticks. Like the stock apps, subtract
    # these frame milliseconds directly; time.ticks_diff only supports
    # tokens returned by time.ticks_ms/us/cpu, not badge frame timestamps.
    def __init__(self, own_id, persist, confirm=None):
        self.own_id = own_id
        self.persist = persist
        self.confirm = confirm
        self.link = badgelink.Link("walking demo")
        if badgelink.badge_id_hex(self.link.id) != own_id:
            self.link.close()
            raise ValueError("Badge-link identity differs from the step counter")
        self.proximity = badgelink.Proximity(self.link)
        self.trace = PairingTrace(self.link)
        self.exchange = None
        self.started = 0
        self.last_send = None
        self.packet_index = 0
        self.completed_at = None
        self.synced_total = None
        self.notice = ""
        self.notice_at = None
        self.peer_id = None
        self.departing = False
        self.waiting_for_apart = False
        self.rest_at = 0
        self.success_at = None

    def _leave(self, now, notice):
        self.trace.record("leave clock", (now, self.started, now - self.started,
                                          self.completed_at, self.last_send, self.notice_at))
        self.trace.record("leave", notice)
        self.proximity.rest(self.peer_id, now)
        self.rest_at = now
        self.waiting_for_apart = True
        self.link.leave()
        self.departing = True
        self.exchange = None
        self.completed_at = None
        self.notice = notice
        self.notice_at = now

    def update(self, now, counts):
        self.trace.now = now
        try:
            self._update(now, counts)
        finally:
            self.trace.observe(self)

    def _update(self, now, counts):
        self.link.pump()
        linked = self.link.linked
        if self.departing:
            if linked:
                self.link.update()
                return
            self.departing = False
        if linked and self.waiting_for_apart:
            self._leave(now, "Move badges apart")
            self.link.update()
            return
        if linked and self.exchange is None and self.link.capacity() < START_CAPACITY:
            self.link.update()
            return
        if linked:
            try:
                if self.exchange is None:
                    self.peer_id = self.link.partner.id
                    capacity = self.link.capacity()
                    self.trace.record("connected", (self.peer_id, capacity))
                    if capacity < PACKET_SIZE:
                        raise ValueError("Badge link cannot fit the step packet")
                    peer_hex = badgelink.badge_id_hex(self.peer_id)
                    self.exchange = Exchange(self.own_id, peer_hex, counts, self.persist)
                    self.success_at = None
                    self.started = now
                    self.last_send = None
                    self.packet_index = 0
                for packet in self.link.receive():
                    self.trace.record("receive", packet)
                    self.exchange.receive(packet)
                # Alternate state and ACK so a small transmit queue cannot
                # starve either packet. Continue ACK retries during the grace period.
                send_age = None if self.last_send is None else now - self.last_send
                if send_age is None or send_age >= 100:
                    self.trace.record("send clock", (now, self.last_send, send_age))
                    packets = self.exchange.packets()
                    packet = packets[self.packet_index % len(packets)]
                    accepted = self.link.send(packet)
                    self.trace.sent(packet, accepted)
                    if accepted:
                        self.last_send = now
                        self.packet_index += 1
                if self.exchange.done:
                    if self.completed_at is None:
                        if self.confirm is not None:
                            self.confirm(self.exchange.counts)
                        self.completed_at = now
                        self.success_at = now
                        self.synced_total = self.exchange.total
                    elif now - self.completed_at >= 1000:
                        self._leave(now, "Synced")
                elif now - self.started >= 8000:
                    self.trace.record("timeout", (now, self.started, now - self.started))
                    self._leave(now, "Hold together to retry")
            except (OSError, ValueError) as error:
                self.trace.record("exchange error", (type(error).__name__, str(error)))
                print("walking: sync failed:", error)
                self._leave(now, "Could not sync - try again")
        elif self.exchange is not None:
            self.trace.record("connection lost", (now, self.started))
            self._leave(now, "Synced" if self.exchange.done else "Hold together to retry")

        # Match Merge Conflict: Proximity owns the idle handshake. Advance
        # the connected protocol only after pump observed an established link.
        if linked:
            self.link.update()
        else:
            self._update_proximity(now)

    def _update_proximity(self, now):
        if self.waiting_for_apart:
            remaining = self.proximity.cooling(now)
            duration = self.proximity.cooldown_ms
            expired = now - self.rest_at >= duration
            if remaining is None and not expired:
                self.waiting_for_apart = False
            elif remaining is None or remaining <= min(1000, duration // 2):
                # Native pairing permits a timed retry. Renew before expiry
                # so only its separation detection can release our gate.
                self.proximity.rest(self.peer_id, now)
                self.rest_at = now
        self.proximity.update(now)
        if self.waiting_for_apart and self.proximity.cooling(now) is None:
            self.waiting_for_apart = False

    def status(self, now):
        if self.completed_at is not None:
            return "Synced"
        if self.exchange is not None:
            return "Syncing..."
        if self.notice_at is not None and 0 <= now - self.notice_at < 3000:
            return self.notice
        if self.waiting_for_apart:
            return "Move badges apart"
        if self.proximity.cooling(now) is not None:
            return "Pull badges apart"
        if self.proximity.syncing() is not None:
            return "Hold steady"
        return "Hold badges back to back"

    def progress(self, now):
        return self.proximity.progress(now) if self.proximity.syncing() is not None else None

    def success_age(self, now):
        if self.success_at is None:
            return None
        age = now - self.success_at
        return age if 0 <= age < 2800 else None

    def lights(self, now):
        if self.link.linked:
            return (0.7 if self.completed_at is not None else 0.25,)
        return self.proximity.lights(now) or (0,)

    def close(self):
        try:
            self.link.close()
        finally:
            self.trace.record("close", None)
            self.trace.save()
