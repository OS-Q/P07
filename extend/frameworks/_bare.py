from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
board_config = env.BoardConfig()

env.Append(
    ASFLAGS=[
        "-x", "assembler-with-cpp"
    ],
    CCFLAGS=[
        "-Os",
        "-fdata-sections",
        "-ffunction-sections",
        "-march=%s" % board_config.get("build.march"),
    ],
    CPPDEFINES=[
        "__riscv__",
        "__pulp__"
    ],
    LINKFLAGS=[
        "-march=%s" % board_config.get("build.march"),
        "-nostartfiles"
    ],
    LIBS=["gcc"],
)

env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])
