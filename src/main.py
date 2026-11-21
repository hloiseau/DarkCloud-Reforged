"""Dark Cloud Reforged
Entry point. Launches the mod window and connects to PCSX2 via PINE IPC.
"""

import argparse
import sys
from core.pine_ipc import PINE_PORT, PineIPC
from core.memory import Memory
from game.game_state import GameState
from ui.app import App


def main():
    import signal

    from mods.ruby_tex import load_textures
    load_textures()

    ipc = PineIPC()
    mem = Memory(ipc)
    state = GameState(mem)

    app = App(state)

    def _quit(*args):
        app._on_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _quit)
    app.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pal", action="store_true", help="European disc preview")
    parser.add_argument("--pine-port", type=int, default=PINE_PORT)
    args = parser.parse_args()
    if args.pal:
        from game.pal import run
        try:
            run(args.pine_port)
        except ValueError as exc:
            parser.exit(1, f"{exc}\n")
        except KeyboardInterrupt:
            pass
    else:
        main()
