import os

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()

RUNTIME_DIR = platform.get_package_dir("framework-pulp-runtime")
assert os.path.isdir(RUNTIME_DIR)

board_config = env.BoardConfig()

env.SConscript("_bare.py")

env.Append(
    ASFLAGS=["-DLANGUAGE_ASSEMBLY"],

    CCFLAGS=[
        "-include", "chips/pulpissimo/config.h",
        "-fno-jump-tables",
        "-fno-tree-loop-distribute-patterns",
        "-U__riscv__"
    ],

    CPPDEFINES=[
        "RV_ISA_RV32",
        ("__PLATFORM__", "ARCHI_PLATFORM_FPGA"),
        ("CONFIG_IO_UART", 0),
        ("CONFIG_IO_UART_BAUDRATE", 115200),
        ("CONFIG_IO_UART_ITF", 0)
    ],

    CPPPATH=[
        os.path.join(RUNTIME_DIR, "include", "chips", "pulpissimo"),
        os.path.join(RUNTIME_DIR, "lib", "libc", "minimal", "include"),
        os.path.join(RUNTIME_DIR, "include"),
        os.path.join(RUNTIME_DIR, "kernel"),
    ]
)

env.AppendUnique(ASFLAGS=env.get("CCFLAGS", [])[:])

if not board_config.get("build.ldscript", ""):
    env.Append(
        LIBPATH=[os.path.join(RUNTIME_DIR, "kernel", "chips", "pulpissimo")]
    )
    env.Replace(LDSCRIPT_PATH="link.ld")

libs = []

libs.append(
    env.BuildLibrary(
        os.path.join("$BUILD_DIR", "kernel"),
        os.path.join(RUNTIME_DIR, "kernel"),
        src_filter=[
            "+<*>",
            "-<cluster.c>",
            "-<chips/>",
            "+<chips/pulpissimo>",
        ],
    )
)

libs.append(
    env.BuildLibrary(
        os.path.join("$BUILD_DIR", "drivers"),
        os.path.join(RUNTIME_DIR, "drivers")
    )
)

libs.append(
    env.BuildLibrary(
        os.path.join("$BUILD_DIR", "lib", "libc", "minimal"),
        os.path.join(RUNTIME_DIR, "lib")
    )
)

env.Append(LIBS=libs)
