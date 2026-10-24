"""Listen to Walking's USB output, reconnecting after a USB interruption.

Run in a local Terminal with pyserial available. Sends no commands to the badge.
"""

import argparse
from contextlib import suppress
from pathlib import Path
import sys
import time

import serial
from serial.tools.list_ports import comports

ROOT = Path(__file__).resolve().parents[1]


def capture(output, seconds):
    output.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + seconds
    connection = None
    device_id = None
    last_notice = None
    with output.open("ab", buffering=0) as log:
        def notice(message):
            nonlocal last_notice
            if message != last_notice:
                data = ("\n[capture] " + message + "\n").encode()
                log.write(data)
                print(data.decode(), end="", flush=True)
                last_notice = message

        notice("Listening for %s seconds. Open Walking on both badges, then hold together." % seconds)
        try:
            while time.monotonic() < deadline:
                if connection is None:
                    ports = [p for p in comports() if (p.vid, p.pid) == (0x2E8A, 0x1101)]
                    if device_id is not None:
                        ports = [p for p in ports if p.serial_number == device_id]
                    if len(ports) != 1:
                        notice("Waiting for one badge over USB...")
                        time.sleep(0.5)
                        continue
                    port = ports[0]
                    try:
                        connection = serial.Serial(port.device, 115200, timeout=0.25, exclusive=True)
                        device_id = port.serial_number
                        notice("Connected: %s (%s)" % (device_id, port.device))
                    except (OSError, serial.SerialException) as error:
                        notice("Waiting to reconnect: " + str(error))
                        time.sleep(0.5)
                        continue
                try:
                    data = connection.read(256)
                except (OSError, serial.SerialException) as error:
                    notice("USB interrupted; reconnecting: " + str(error))
                    with suppress(OSError, serial.SerialException):
                        connection.close()
                    connection = None
                    time.sleep(0.5)
                    continue
                if data:
                    log.write(data)
                    sys.stdout.write(data.decode("utf-8", errors="replace"))
                    sys.stdout.flush()
        except KeyboardInterrupt:
            pass
        finally:
            if connection is not None:
                with suppress(OSError, serial.SerialException):
                    connection.close()
        notice("Finished. Log saved to " + str(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--output", type=Path, default=ROOT / "diagnostics/pairing-live.log")
    args = parser.parse_args()
    capture(args.output, args.seconds)
