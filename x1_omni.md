# notes for X1 Omni

<https://robotinfo.dev/detail_ecovacs.1vxt52_0.html>


## info / misc

Horizon X3M SoC `Linux deboot 4.14.74 #1 SMP PREEMPT Sat Sep 3 10:54:50 CST 2022 aarch64 GNU/Linux`

serial number gets dumped in bootup phase, as well as MQTT config and some secrets

TODO find where they live


## how to get root

i was able to do it on updated firmware. YMMV.

* reverse the diagram 180 degrees given by Dennis
    * so gnd on the side closest to the micro usb
    * tx/rx on the other side
* plug in USB, connect, then switch on
    * e.g. for me `sudo minicom -D /dev/ttyUSB0 -C capture.txt`
* root password: <https://builder.dontvacuum.me/ecopassword.php>

## networking

### hosts

* 			"default_lb_srv":"lb.ecouser.net",
* 					"lb_srv":"mq.ecouser.net",
* 			"domain_china":"portal.ecouser.net",
* 			"domain_others":"portal-ww.ecouser.net"


## software

### cjp

`cjp` can read some data and files

```
ret=$(cat /tmp/config.bin)
enable=$(cjp "${ret}" int voice)

DEVICE_INFO=`mdsctl sys0 "{\"pid_get\":\"get_all\"}"`
SN=`cjp "${DEVICE_INFO}" string sn`
```

### random scripts

* `/usr/bin/get_bd_quadruples.sh`
    * `/etc/rc.d/speech_recognition.sh`
    * speech recognition?

* `/usr/bin/eros_data_upload.sh`
    * uploading telemetry data?
* `/usr/bin/factory_reset.sh`
* `/usr/bin/fw_upgrade.sh`
    * firmware updater??
* `/usr/bin/fw_cut.sh`
    * firmware updater?
    * `FW_FILE=/data/fw.bin             `
    * mcu update?
```bash
mdsctl rosnode '{"todo":"mcuota","type":3,"act":"start"}'
mdsctl rosnode '{"todo":"mcuota","type":0,"act":"start"}'
sleep 1.5
mdsctl "mcuota" '{"todo": "fw_mcu", "cmd": "mcu_upgrade_start", "file_path":"/tmp/mcu.bin"}'
```
    * 

### utils

* `/usr/bin/factory_fun` bash utils (in `/usr/bin` for some reason)
    * valuable source of info
* `netmon_ctl` communicates to socket and sends json?
    * `netmon_ctl -s /tmp/audio_daemon.sock -j "{\"fileList\":[{\"path\":\"${FILE}\"}],\"audioType\":3}"`
* `mdsctl`
    * `mdsctl audio0 "{\"todo\":\"audio\", \"cmd\":\"play\",\"file_number\":$1}" &`
    * `mdsctl bumbee "{\"todo\":\"QueryIotInfo\"}"` passwords?
* `cjp` data parser?

### facial / person detection ?

from medusa logs:
```
[2024-07-01 11:25:26 INFO 548221251600 hr_api.cpp:479] HorizonRT version = 1.6.4
[2024-07-01 11:25:26 INFO 548221251600 hr_api.cpp:484] hbrt version = 3.12.6
```

https://github.com/Lin-lucky/intron_horizon_ai_toolchain/blob/19857964e1bec0b724881cfaa1885e5a03571509/doc/cn/_sources/common_doc_cn/xj3_ddk_sample.rst.txt#L196

### ota

   see the deebot_x3 conf
   			"fw_file_name":"/data/fw.bin",
			"fw_config_path":"/data/config/medusa/enableAutoOta.conf",

### medusa

similar to `ava` on the dreames

* short names: `md`
* possible config file: `/tmp/deebot_x3.conf`
* `mdsctl` to communicate to daemon, similar to `avacmd`
* socket: `/tmp/mds_cmd.sock`
* config? `/tmp/log/md.log`

possibly some config in `/dev/ubi2_0` with file offsets?
`			"joylink_tiot_parameters_offset":10240,`


take a look at:
* 			"lds_config_file_path":"/tmp/config.bin",
* FW_LOG_FILE=/data/log/fw.log


## dumping files

easy as it has dd and netcat. same old same old

```bash
dd if=/dev/ubiblock0_0 | nc 192.168.88.7 6969
nc -l -p 6969 | dd of=ubiblock0_0.img
```

as it has curl, you can also use:
* `python3 -m http.server 6969 -d upload` and serve a folder
* or <https://github.com/Hypfer/valetudo-helper-httpbridge>


## devices

* `/dev/ubi0_0` - rootfs
* `/dev/ubi1_0` - `/data`
* `/dev/ubi2_0` - `SYSINFO` device 
  * `SYSINFO_DEV=/dev/ubi2_0` from `/usr/bin/factory_fun`
  * a lot of offsets used to pull data from this device
* `/dev/ttyS0` - `MCU_TTY` the MCU
  * example of writing to MCU (commented out)
  * `#echo -en '\x60\x53\x41\x00\x11\xc2\x44\x69\x43\x49\x02\xac\x0a' > /dev/ttyS1  #inform muc to reboot`
  * 

```bash
Filesystem                Size      Used Available Use% Mounted on
/dev/root                79.4M     79.4M         0 100% /
devtmpfs                334.9M         0    334.9M   0% /dev
tmpfs                   493.4M     91.7M    401.7M  19% /tmp
run                     493.4M     80.0K    493.3M   0% /run
none                    493.4M     16.0K    493.3M   0% /dev/shm
/dev/ubi1_0             148.9M      7.6M    141.3M   5% /data
/dev/ubiblock3_0         68.1M     68.1M         0 100% /model
```


### rootfs

rootfs is `/dev/ubiblock0_0` and `squashfs`

found in kernel command-line parameters

```
bash-4.4# cat /proc/cmdline
earlycon kgdboc=ttyS0 console=ttyS0,115200 raid=noautodetect hobotboot.reson=POWER_RESET ubi.mtd=5 ubi.block=0,rootfs,4096 root=/dev/ubiblock0_0 rootfstype=squashfs ro rootwait mtdparts=hr_na
```

see `repack_rootfs.txt` from Telegram on how to rewrite (NOT TESTED)


## cron

TODO

`/usr/bin/autoOTA.sh`


## getting ssh

TODO

getting dropbear setup easily was a pain cause ARM64 and glibc version mismatching.

i static compiled my own version based on the INSTALL doc <https://github.com/mkj/dropbear/blob/master/INSTALL.md> and threw it into `/data`

after installing and running, you get slapped with this:

```
bash-4.4# ./dropbear -r /data/dropbear/rsa -F
[4286] Jul 01 13:31:30 Not backgrounding
[4098] Jul 01 13:31:39 Exit before auth from <192.168.88.7:34654>: (user 'root', 2 fails): Exited normally
[4297] Jul 01 13:31:40 Child connection from 192.168.88.7:53874
[4297] Jul 01 13:31:40 User 'root' has invalid shell, rejected
```

looks like `/bin/sh` is missing from `/etc/shells`

as rootfs is read-only, we need to flash it and install dropbear, and do some tweaks (maybe change login shell to bash)

another option might be using an sshd which does not check `/etc/shells` or doing some `bubblewrap`

either way need to flash the rootfs at some stage, and there's docs on how, so try out later

TODO
