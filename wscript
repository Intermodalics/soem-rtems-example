# Copyright 2017 Intermodalics
# Original author: Kevin De Martelaere <kevin.demartelaere@intermodalics.eu>
#
# Top level waf build script for rtems-soem
#
## Configure
# waf configure --prefix=$RTEMS_BSPS --rtems-tools=$RTEMS_TOOLS --rtems-bsps=arm/xilinx_zynq_a9_qemu --rtems-version=$RTEMS_VER
#
## Build
# waf
#

rtems_version = "4.11"
try:
    import rtems_waf.rtems as rtems
except:
    print 'error: no rtems_waf git submodule; see README.waf'
    import sys
    sys.exit(1)

def init(ctx):
    rtems.init(ctx, version = rtems_version, long_commands = True)

def options(opt):
    rtems.options(opt)
    opt.add_option('--enable-warnings',
                   action = 'store_true',
                   default = False,
                   dest = 'warnings',
                   help = 'Enable all warnings. The default is quiet builds.')

def bsp_configure(conf, arch_bsp):
    conf.check(lib='bsd', uselib='BSD', define_name='HAVE_LIBBSD')
    conf.check(header_name="rtems/rtems_bsdnet.h", features="c", madatory=True)
    conf.env.DEFINES_BSD   = ['BSD']
    conf.env.LIB_BSD       = ['bsd']

    conf.check(lib='soem', uselib='SOEM', define_name='HAVE_LIBSOEM')
    conf.check(header_name="soem/ethercat.h", features="c", mandatory=True)
    conf.env.DEFINES_SOEM  = ['SOEM']
    conf.env.LIB_SOEM      = ['soem']

def configure(conf):
    rtems.configure(conf, bsp_configure)
    conf.env.WARNINGS = conf.options.warnings

def set_common_env_values(bld):
    bld.env.CFLAGS += ['-O2']
    bld.env.CFLAGS += ['-g']
    bld.env.LDFLAGS += ['-Wl,--defsym']
    bld.env.LDFLAGS += ['-Wl,HeapSize=0x80000']
    if bld.options.warnings:
      bld.env.CFLAGS += ['-Wall']
      bld.env.CFLAGS += ['-Wextra']

def build(bld):
    rtems.build(bld)

    set_common_env_values(bld)

    bld.recurse('tests')

def rebuild(ctx):
    import waflib.Options
    waflib.Options.commands.extend(['clean', 'build'])

def tags(ctx):
    ctx.exec_command('etags $(find . -name \*.[sSch])', shell = True)
