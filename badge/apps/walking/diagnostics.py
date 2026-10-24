"""Keep the latest error available for a local serial read if a test fails."""

import io
import sys


def capture(stage, error):
    brief = type(error).__name__ + ": " + str(error)
    print("walking:", stage, brief)
    try:
        trace = io.StringIO()
        printer = getattr(sys, "print_exception", None)
        if printer is not None:
            printer(error, trace)
        else:
            trace.write(brief)
        with open("/state/walking_error.txt", "w") as file:
            file.write(stage + "\n" + trace.getvalue())
    except Exception:
        pass
    return brief
