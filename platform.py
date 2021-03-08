from os.path import join

from platformio.managers.platform import PlatformBase
from platformio.util import get_systype


class P02Platform(PlatformBase):

    def configure_default_packages(self, variables, targets):
        if "zephyr" in variables.get("pioframework", []):
            for p in self.packages:
                if p.startswith("framework-zephyr-") or p in (
                    "tool-cmake",
                    "tool-dtc",
                    "tool-ninja"
                ):
                    self.packages[p]["optional"] = False
            if "windows" not in get_systype():
                self.packages["tool-gperf"]["optional"] = False

        return PlatformBase.configure_default_packages(self, variables, targets)

    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        if "tools" not in debug:
            debug["tools"] = {}

        tools = (
            "digilent-hs1",
            "olimex-arm-usb-tiny-h",
            "olimex-arm-usb-ocd-h",
            "olimex-arm-usb-ocd",
            "olimex-jtag-tiny",
            "verilator",
            "whisper"
        )
        for tool in tools:
            if tool in debug["tools"]:
                continue
            server_executable = "bin/openocd"
            server_package = "tool-openocd-riscv-chipsalliance"
            server_args = [
                "-s",
                join(
                    self.get_package_dir("framework-wd-riscv-sdk") or "",
                    "board",
                    board.get("build.variant", ""),
                ),
                "-s",
                "$PACKAGE_DIR/share/openocd/scripts",
            ]
            reset_cmds = [
                "define pio_reset_halt_target",
                "   load",
                "   monitor reset halt",
                "end",
                "define pio_reset_run_target",
                "   load",
                "   monitor reset",
                "end",
            ]
            if tool == "verilator":
                openocd_config = join(
                    self.get_dir(),
                    "misc",
                    "openocd",
                    board.get("debug.openocd_board", "swervolf_sim.cfg"),
                )
                server_args.extend(["-f", openocd_config])
            elif tool == "whisper":
                server_executable = "whisper"
                server_package = "tool-whisper"
                server_args = [
                    "--gdb",
                    "--gdb-tcp-port=3333",
                    "--configfile=$PACKAGE_DIR/whisper_eh1.json",
                    "--alarm=100",
                    "--consoleio=0x80002000",
                    "--counters",
                    "$PROG_PATH"
                ]
                reset_cmds = [
                    "define pio_reset_halt_target",
                    "end",
                    "define pio_reset_run_target",
                    "end",
                ]
            elif debug.get("openocd_config", ""):
                server_args.extend(["-f", debug.get("openocd_config")])
            else:
                assert debug.get("openocd_target"), (
                    "Missing target configuration for %s" % board.id
                )
                # All tools are FTDI based
                server_args.extend(
                    [
                        "-f",
                        "interface/ftdi/%s.cfg" % tool,
                        "-f",
                        "target/%s.cfg" % debug.get("openocd_target"),
                    ]
                )
            debug["tools"][tool] = {
                "init_cmds": reset_cmds + [
                    "set mem inaccessible-by-default off",
                    "set arch riscv:rv32",
                    "set remotetimeout 250",
                    "target extended-remote $DEBUG_PORT",
                    "$INIT_BREAK",
                    "$LOAD_CMDS",
                ],
                "server": {
                    "package": server_package,
                    "executable": server_executable,
                    "arguments": server_args,
                },
                "onboard": tool in debug.get("onboard_tools", [])
                or tool in ("verilator", "whisper"),
            }

        board.manifest["debug"] = debug
        return board
