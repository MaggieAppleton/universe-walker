"""Walk independently, then hold two badges together to combine progress."""

import binascii
import machine
import os
import sys
import time

APP_DIR = "/system/apps/walking"
os.chdir(APP_DIR)
sys.path.insert(0, APP_DIR)

from badgeware import State
from progress import merge_counts, display_totals
from steps import StepCounter
from boost import HoldBoost, room
from sync_protocol import GAME_ID
from diagnostics import capture

STATE_KEY = "walking_demo"
DEVICE_ID = binascii.hexlify(machine.unique_id()).decode()
state = {"counts": {DEVICE_ID: 0}, "game": GAME_ID, "last_sync": {}}
State.load(STATE_KEY, state)
if state["game"] != GAME_ID:
    raise ValueError("A different walking game is saved on this badge")
counts = merge_counts({DEVICE_ID: 0}, state["counts"])
counter = StepCounter(counts[DEVICE_ID])
last_sync = merge_counts({}, state["last_sync"])
boost = HoldBoost()

badge.mode(HIRES | VSYNC)
import walking_ui as ui
ui.set_badge(DEVICE_ID)
badge.default_clear = ui.BACKGROUND

sensor_bus = None
sensor_failed = False
save_failed = False
dirty = False
last_poll = time.ticks_ms()
last_save = last_poll
fatal_message = None

try:
    # Verified 2026 wiring: onboard IMU on I2C1, GPIO18/19, address 0x6A.
    sensor_bus = machine.I2C(1, sda=machine.Pin(18), scl=machine.Pin(19), freq=400000)
    if sensor_bus.readfrom_mem(0x6A, 0x0F, 1)[0] != 0x6A:
        raise ValueError("Unexpected IMU identity")
    if sensor_bus.readfrom_mem(0x6A, 0x19, 1)[0] & 0x14 != 0x14:
        raise ValueError("Hardware pedometer is disabled")
except Exception as error:
    print("walking: sensor setup failed:", error)
    sensor_bus = None
    sensor_failed = True


def store_progress(merged, shared):
    global dirty, save_failed, last_save
    saved_counts, saved_sync = dict(merged), dict(shared)
    State.save(STATE_KEY, {"counts": saved_counts, "game": GAME_ID, "last_sync": saved_sync})
    counts.clear()
    counts.update(saved_counts)
    last_sync.clear()
    last_sync.update(saved_sync)
    counter.total = max(counter.total, counts[DEVICE_ID])
    dirty = False
    save_failed = False
    last_save = time.ticks_ms()


def save_progress():
    global save_failed, last_save
    if not dirty:
        return
    try:
        store_progress(counts, last_sync)
    except OSError as error:
        print("walking: could not save:", error)
        save_failed = True
    last_save = time.ticks_ms()


def save_sync(snapshot):
    store_progress(merge_counts(counts, snapshot), last_sync)


def confirm_sync(snapshot):
    store_progress(merge_counts(counts, snapshot), snapshot)


# Optional live-dashboard status; pairing works the same without it. It must
# wrap the radio before Link exists, because Link advertises when created.
beacon = None
try:
    from badgeware import link as badgelink
    from status_beacon import Beacon
    beacon = Beacon(badgelink.radio, None, DEVICE_ID)
except Exception as error:
    print("walking: status beacon unavailable:", error)

sync = None
try:
    from sync_link import BadgeSync
    sync = BadgeSync(DEVICE_ID, save_sync, confirm_sync)
except Exception as error:
    capture("sync setup", error)
if beacon is not None:
    if sync is None:
        beacon.close()
        beacon = None
    else:
        beacon.link = sync.link


def stop_beacon():
    global beacon
    active, beacon = beacon, None
    if active is not None:
        try:
            active.close()
        except Exception as error:
            print("walking: status beacon close failed:", error)


def publish_status(*screen):
    if beacon is None:
        return
    try:
        beacon.publish(*screen)
    except Exception as error:
        print("walking: status beacon stopped:", error)
        stop_beacon()


def stop_sync():
    global sync
    stop_beacon()
    active, sync = sync, None
    if active is not None:
        try:
            active.close()
        except Exception as error:
            print("walking: link close failed:", error)
    badge.caselights(0)


def update_frame():
    global dirty, last_poll, sensor_failed, sync
    now = time.ticks_ms()
    if sensor_bus is not None and time.ticks_diff(now, last_poll) >= 250:
        last_poll = now
        try:
            raw = sensor_bus.readfrom_mem(0x6A, 0x4B, 2)
            if counter.update(raw[0] | (raw[1] << 8)):
                counts[DEVICE_ID] = counter.total
                dirty = True
            sensor_failed = False
        except OSError as error:
            if not sensor_failed:
                print("walking: sensor read failed:", error)
            sensor_failed = True
    added = boost.update(badge.pressed(BUTTON_UP) or badge.held(BUTTON_UP), badge.ticks)
    added = min(added, room(counter.total, last_sync.get(DEVICE_ID, 0)))
    if added:
        counter.total += added
        counts[DEVICE_ID] = counter.total
        dirty = True
    if dirty and time.ticks_diff(now, last_save) >= 2000:
        save_progress()
    status, progress, success_age, success_total = "Sync paused - reopen Walking", None, None, None
    if sync is not None:
        try:
            sync.update(badge.ticks, counts)
            badge.caselights(*sync.lights(badge.ticks))
            status = sync.status(badge.ticks)
            progress = sync.progress(badge.ticks)
            success_age = sync.success_age(badge.ticks)
            success_total = sync.synced_total
        except Exception as error:
            stop_sync()
            capture("sync update", error)
    if sensor_failed:
        status = "Step sensor unavailable"
    elif save_failed:
        status = "Progress not saved"
    own, team, partner = display_totals(DEVICE_ID, counts, last_sync)
    publish_status(own, team, partner, status, progress,
                   success_total if success_age is not None else None)
    ui.draw(own, team, partner, status, progress, success_age, success_total)


def update():
    global fatal_message
    if fatal_message is not None:
        ui.error(fatal_message)
        return
    try:
        update_frame()
    except Exception as error:
        fatal_message = capture("app frame", error)
        save_progress()
        stop_sync()
        ui.error(fatal_message)


def on_exit():
    save_progress()
    stop_sync()


run(update)
