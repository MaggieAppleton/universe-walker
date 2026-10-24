"""Small durable exchange; the native link supplies the partner identity."""

import struct

from progress import merge_counts

GAME_ID = 0x2026
VERSION = 1
STATE = 1
ACK = 2
FORMAT = "<BBHII"
PACKET_SIZE = struct.calcsize(FORMAT)


class Exchange:
    def __init__(self, own_id, peer_id, counts, persist):
        if own_id == peer_id or not own_id or not peer_id:
            raise ValueError("Two different badges are required")
        if set(counts) - {own_id, peer_id}:
            raise ValueError("Already walking with another badge")
        self.own_id = own_id
        self.peer_id = peer_id
        self.persist = persist
        self.snapshot = merge_counts({own_id: 0, peer_id: 0}, counts)
        if any(count > 0xFFFFFFFF for count in self.snapshot.values()):
            raise ValueError("Step count exceeds the packet range")
        self.counts = None
        self.pending_ack = None
        # Save existing progress before publishing it. Bind the peer only
        # after actually receiving its snapshot, not merely discovering it.
        self.persist(dict(counts))

    def _packet(self, kind, counts):
        return struct.pack(FORMAT, kind, VERSION, GAME_ID,
                           counts[self.own_id], counts[self.peer_id])

    def packets(self):
        packets = [self._packet(STATE, self.snapshot)]
        if self.counts is not None:
            packets.append(self._packet(ACK, self.counts))
        return packets

    def receive(self, packet):
        if len(packet) != PACKET_SIZE:
            raise ValueError("Unexpected sync packet size")
        kind, version, game_id, theirs, remembered_mine = struct.unpack(FORMAT, packet)
        if version != VERSION or game_id != GAME_ID or kind not in (STATE, ACK):
            raise ValueError("Different walking game")
        incoming = {self.peer_id: theirs, self.own_id: remembered_mine}
        if kind == ACK:
            if self.counts is None or incoming == self.counts:
                self.pending_ack = incoming
            return
        merged = merge_counts(self.snapshot, incoming)
        if self.counts is not None and merged != self.counts:
            raise ValueError("Snapshot changed during sync")
        if self.counts is None:
            # A failed write must leave counts unset so no ACK can be sent.
            self.persist(merged)
            self.counts = merged

    @property
    def done(self):
        return self.counts is not None and self.pending_ack == self.counts

    @property
    def total(self):
        return sum(self.counts.values()) if self.counts is not None else None
