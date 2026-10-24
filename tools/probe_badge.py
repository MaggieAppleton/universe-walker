"""Inspect runtime and hardware APIs; may initialize display and IMU hardware."""

import binascii
import builtins
import machine
import os
import sys

print("FIRMWARE:", sys.implementation)
print("BOARD:", os.uname())
print("DEVICE_ID:", binascii.hexlify(machine.unique_id()).decode())

badge_device = globals().get("badge") or getattr(builtins, "badge", None)
if badge_device is None:
    try:
        import badgeware
        print("RUNTIME_EXPORTS:", dir(badgeware))
        print("RUNTIME_FILE:", getattr(badgeware, "__file__", "frozen"))
        badge_device = getattr(builtins, "badge", None)
        if badge_device is None:
            badge_device = getattr(badgeware, "badge", None)
    except Exception as error:
        print("RUNTIME_INIT_ERROR:", repr(error))
        sys.print_exception(error)
print("BADGE_RUNTIME:", badge_device is not None)
if badge_device is not None:
    print("MOTION_APIS:", [name for name in dir(badge_device)
                          if "imu" in name or "step" in name])
    try:
        print("IMU_SAMPLE:", badge_device.imu())
    except Exception as error:
        print("IMU_READ_ERROR:", repr(error))
    imu = getattr(badge_device, "_imu", None)
    print("IMU_DRIVER:", type(imu).__name__ if imu is not None else "unavailable")
    if imu is not None:
        reader = getattr(imu, "get_step_count", None)
        print("HARDWARE_PEDOMETER:", callable(reader))
        if callable(reader):
            try:
                print("HARDWARE_STEP_COUNT:", reader() & 0xFFFF)
            except Exception as error:
                print("PEDOMETER_READ_ERROR:", repr(error))

# The custom 2026 board uses I2C1 on GPIO18/19, with its IMU at 0x6A.
# Sources: badger/home/hardware/README.md and ST LSM6DS3TR-C datasheet,
# registers WHO_AM_I (0x0F), CTRL1_XL (0x10), CTRL10_C (0x19),
# STEP_COUNTER_L/H (0x4B/0x4C). No sensor configuration writes are made.
try:
    print("SENSOR_POWER_PIN:", machine.Pin(41).value())
    sensor_bus = machine.I2C(1, sda=machine.Pin(18), scl=machine.Pin(19), freq=400000)
    chip_id = sensor_bus.readfrom_mem(0x6A, 0x0F, 1)[0]
    print("IMU_CHIP_ID:", hex(chip_id), "expected 0x6a")
    if chip_id == 0x6A:
        accel_config = sensor_bus.readfrom_mem(0x6A, 0x10, 1)[0]
        function_config = sensor_bus.readfrom_mem(0x6A, 0x19, 1)[0]
        raw_steps = sensor_bus.readfrom_mem(0x6A, 0x4B, 2)
        print("ACCEL_CONFIG:", hex(accel_config))
        print("FUNCTION_CONFIG:", hex(function_config))
        print("PEDOMETER_ENABLED:", (function_config & 0x14) == 0x14)
        print("DIRECT_STEP_COUNT:", raw_steps[0] | (raw_steps[1] << 8))
except Exception as error:
    print("DIRECT_SENSOR_ERROR:", repr(error))

try:
    import bluetooth
    radio = bluetooth.BLE()
    print("BLUETOOTH_ACTIVE:", radio.active())
    for method in ("gap_scan", "gap_advertise", "gap_connect",
                   "gatts_register_services", "gattc_read", "gattc_write"):
        print("BLE_API:", method, hasattr(radio, method))
except Exception as error:
    print("BLUETOOTH_ERROR:", repr(error))

print("PROBE_COMPLETE")
