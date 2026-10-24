"""Keep a bounded pairing trace and checkpoint it without relying on HOME."""


class PairingTrace:
    def __init__(self, link, path="/system/apps/walking/pairing-trace.log"):
        self.path = path
        self.lines = []
        self.omitted = 0
        self.now = 0
        self.previous = None
        self.previous_send = None
        self.saved_at = None
        self.original_journal = getattr(link, "journal", None)
        link.journal = self.journal
        self.record("start", getattr(link, "id", None))

    def record(self, kind, value):
        try:
            line = "%s %s %s" % (self.now, kind, repr(value)[:240])
            if len(self.lines) >= 128:
                self.lines.pop(0)
                self.omitted += 1
            self.lines.append(line)
        except Exception:
            pass

    def journal(self, kind, value):
        if self.original_journal is not None:
            value = self.original_journal(kind, value)
        try:
            if kind == "ble":
                for event in value:
                    # Scan results include unrelated nearby devices. Keep
                    # connection/GATT events, not advertisements or scan ends.
                    if event[0] not in (5, 6):
                        self.record("radio", event)
        except Exception:
            pass
        return value

    def observe(self, sync):
        try:
            value = (sync.status(self.now), sync.link.linked,
                     getattr(sync.link, "linking", None),
                     sync.link.capacity() if sync.link.linked else None,
                     getattr(getattr(sync.link, "partner", None), "id", None),
                     getattr(sync.proximity, "sync_id", None),
                     round(sync.progress(self.now) or 0, 1),
                     sync.waiting_for_apart)
            if value != self.previous:
                self.record("state", value)
                self.previous = value
        except Exception as error:
            self.record("trace observation error", str(error))
        if self.saved_at is None or self.now - self.saved_at >= 2000:
            self.save()
            self.saved_at = self.now

    def sent(self, packet, accepted):
        value = (packet, accepted)
        if value != self.previous_send:
            self.record("send", value)
            self.previous_send = value

    def save(self):
        paths = [self.path]
        if self.path == "/system/apps/walking/pairing-trace.log":
            paths.append("/state/walking_pairing.log")
        for path in paths:
            try:
                with open(path, "w") as file:
                    file.write("Walking pairing trace v2; earlier events omitted: %s\n" % self.omitted)
                    file.write("time status linked linking capacity partner proximity progress waiting_apart\n")
                    file.write("\n".join(self.lines) + "\n")
                self.path = path
                return True
            except Exception:
                pass
        return False
