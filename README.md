# SOEM - RTEMS Example
This guide aims at providing a step-by-step procedure on how to install RTEMS, compile the SOEM library and run an example application provided in this repository. This example assumes that the process is performed in an Ubuntu 16.04 host.

## RTEMS Installation
Initially one must get the RTEMS source code and compile a toolchain for compiling for the specific platform that will be used to deploy the application. Then the kernel for the

The first step is to create the top level RTEMS directory and export its location as RTEMS given the following commands:
```
mkdir rtems
cd rtems
export RTEMS=$(pwd)
```
Next the rtems-source-builder should be cloned and the 4.11 branch needs to be checked out:
```
git clone git://git.rtems.org/rtems-source-builder.git
cd rsb
git checkout 4.11
export RTEMS_VER=4.11
export RTEMS_SB=$(pwd)/source-builder
cd rtems
```
Check that all the dependencies are installed by running:
```
$RTEMS_SB/sb-check
```
If anything is missing, it should be installed before compiling the toolchain.

Finding the available build sets for the target processor families can be done by running the following command:
```
$RTEMS_SB/sb-set-builder --list-bsets
```
For the rest of the guide an ARM toolchain will be used as given from `4.11/rtems-arm.bset`.

Following the toolchain must be built and exported to the path. This is done with the following commands:
```
export RTEMS_TOOLS=$RTEMS/tools/$RTEMS_VER
$RTEMS_SB/sb-set-builder --log=l-arm.txt --prefix=$RTEMS_TOOLS 4.11/rtems-ARM
export PATH=$RTEMS_TOOLS/bin:$PATH
```

Next the kernel must be built for the correct processor/board. Initially the kernel source must be cloned and the correct branch chosen. This is done with the following commands:
```
cd $RTEMS
mkdir rtems-src
cd rtems-src
git clone git://git.rtems.org/rtems.git
cd rtems
git checkout $RTEMS_VER
```

The next step requires to bootstrap the kernel and is done as explained below:
```
./bootstrap -c
./bootstrap -p
$RTEMS_SB/sb-bootstrap
```

As mentioned earlier the kernel must be built for the correct board. Getting the full list of the available board support packages (bsps) is achieved by running:
```
$RTEMS/rtems-src/rtems/rtems-bsps
```

For this example the `xilinx_zynq_a9_qemu` bsp will be used. For that a directory has to be created for the specific bsp in the `rtems-src` directory. This is done as follows:
```
cd $RTEMS/rtems-src
mkdir xilinx_zynq_a9_qemu
cd xilinx_zynq_a9_qemu
```

Configuring the kernel for the specific bsp is done with the following commands. The `--enable-POSIX` flag is used to enable the RTEMS POSIX library support, while the `--disable-networking` flag is used as the networking stack of `RTEMS-libbsd` will be used.
```
export RTEMS_BSPS=$RTEMS/bsps/$RTEMS_VER
$RTEMS/rtems-src/rtems/configure --prefix=$RTEMS_BSPS --target=arm-rtems4.11 --enable-rtemsbsp=xilinx_zynq_a9_qemu --enable-posix --disable-networking
```

Finally, the kernel should be compiled and installed. This is done by the following set of commands. Issuing the commands will instal the kernel related files in `$RTEMS_BSPS`.
```
make
make install
```

## RTEMS-libbsd Installation
As already mentioned, the networking capabilities will be provided by `RTEMS-libbsd`. This library uses the `waf` build system, therefore to compile and install it, it is required to have `waf` installed. This is done as follows:
```
mkdir -p $HOME/local/bin
wget -P $HOME/local/bin https://waf.io/waf-2.0.4
export WAF=$HOME/local/bin/waf-2.0.4
chmod u+x $WAF
```

To build the `RTEMS-libbsd` first it must be cloned and the branch matching the targeted version must be chosen. In addition the submodules must be initialised. This is done as follows:
```
cd $RTEMS/rtems-src
git clone git://git.rtems.org/rtems-libbsd.git
cd rtems-libbsd
git checkout $RTEMS_VER
git submodule init
git submodule update rtems_waf
```

Configuring, building and installing `RTEMS-libbsd` is performed using the following commands:
```
$WAF configure --prefix="$RTEMS_BSPS" --rtems-tools="$RTEMS_TOOLS" --rtems-bsps=arm/xilinx_zynq_a9_qemu --rtems-version=$RTEMS_VER
$WAF
$WAF install
```

## Building the SOEM library
The next step requires the SOEM library. This is done as follows:
```
cd $RTEMS/rsb/rtems
$RTEMS_SB/sb-set-builder --log=log_arm_soem --prefix=$RTEMS_BSPS --with-tools=$RTEMS_TOOLS --target=arm-rtems4.11 --with-rtems-bsp=xilinx_zynq_a9_qemu $RTEMS_VER/net/soem
```

## Building the example application
To build the example application first the source should be cloned as follows:
```
cd $RTEMS/rtems-src
git clone git://github.org/intermodalics/soem-rtems.git
cd soem-rtems
```

The example also uses the waf build system so configuration and building is performed in a similar manner as the `RTEMS-libbsd`:
```
$WAF configure --prefix=$RTEMS_BSPS --rtems-tools=$RTEMS_TOOLS --rtems-bsps=arm/xilinx_zynq_a9_qemu --rtems-version=$RTEMS_VER
$WAF
```

## Running the example application
To run the example application the QEMU emulator will be used and it will communicate with the EtherCAT slaves using a physical ethernet interface.

### Building QEMU
A newer version of QEMU is required than the one provided by Ubuntu. Therefore it will be built from source. This is done by following the next commands:
```
cd $RTEMS/rtems-src
git clone git://git.qemu.org/qemu.git
cd qemu
git checkout stable-2.10
git submodule init
git submodule update --recursive
./configure --prefix=$RTEMS_TOOLS --target-list=arm-softmmu
make all install
```

### Network configuration
To be able to connect the emulated device with a physical networking interface a `bridge` and a `tap` interface is required.

First a bridge is created by issuing the following command:
```
sudo ip link add br0 type bridge
```

Following the ip traffic is disabled in the required ethernet interface and is linked to the bridge by:
```
sudo ip addr flush dev eth0
sudo ip link set eth0 master br0
```

A tap can be created and linked to the bridge by the following commands:
```
sudo tunctl -u $(whoami)
sudo ip link set tapX master br0 # Where tapX is the tap name returned by the previous command
```

Finally the bridge and tap interfaces are brought up by:
```
sudo ip link set dev br0 up
sudo ip link set dev tapX up
```

### Running the application
Finally to run the application the EtherCAT slaves must be connected to the interface and the following commands should be executed in two different terminals in that order:

Terminal 1:
```
netcat -l 12456
```

Terminal 2:
```
cd $RTEMS/rtems-src/soem-rtems/build/arm-rtems4.11-xilinx_zynq_a9_qemu/tests/slaveinfo
qemu-system-arm -nographic -serial stdio -serial mon:tcp:localhost:12456 -M xilinx-zynq-a9 -net nic,model=cadence_gem,macaddr=0e:b0:ba:5e:ba:11 -net tap,ifname=tapX,script=no,downscript=no -m 256M -kernel slaveinfo.exe # Where tapX is the tap interface previously created.
```

This will run the slaveinfo application and information regarding the connected slaves will be print on the screen.
