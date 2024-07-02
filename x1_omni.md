# notes for X1 Omni

<https://robotinfo.dev/detail_ecovacs.1vxt52_0.html>


## TODO

1. look at each init script
2. run this `mdsctl bumbee "{\"todo\":\"QueryIotInfo\"}"`
    * ubi0_0/etc/conf/medusa/send_token_to_eco_iot.sh

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

* a lot of calls to `api-rapp.cn.ecouser.net` to get baidu data
* and main endpoint is `jmq-ngiot-au.area.ww.ecouser.net`

## services (socket files)

(from `factory.conf`)
* "unix_wifi_server":"/tmp/netmon.sock"
* "unix_medusa_server":"/tmp/mds_cmd.sock"

## listening services (ports)

* `audio_daemon` ??
    * port 8081
    * `/etc/conf/audio_daemon.conf`
```
"unixSockPath":         "/tmp/audio_daemon.sock",
"ipaddr":               "127.0.0.1",
"port":                 8081,
```
* `ROS` master = http://localhost:11311
    * `/tmp/log/roslog`



## fs (draft)

* etc/
    * cam/
        * some .so files that seem related to camera sensor models
    * conf/
        * `adbkey.pub` developers personal SSH pub key? `richard@OptiPlex` needed for android/ADB?
        * `dxai_*.json` seems to be related to ROS
            * `dxai_node.json`
            * `dxai_ota.json`
        * `eco_passwd.conf` config for `eco_passwd` command? points to `/tmp/sys.bin` to get serial number
        * medusa/
            * `deebot_x3.conf`
                * seems like the most important config file
    * rc.d/
        * lots of scripts that _may_ run on autostart
        * e.g. ROS
    * www/
        * web server
    * `hosts` symlinked to `/tmp/root/etc/hosts` so it can be updated
        * set in `pre_boot.sh` `init.d` script

    * `fw.manifest` - info on the firmware installed. JSON

* tmp/
    * `config.bin` from `/etc/rc.d/post_boot.sh`, `ubi_read` on `ubi2_0`

* data/
    * `/data/config/medusa/defIot.json` from `/etc/rc.d/post_boot.sh`

## button presses?

* `/etc/conf/key-service.conf` to setup `hook` shell scripts


## software

### MQTT

* `mq-ww.ecouser.net`

### some XMPP references

* `mds_wukong_get_best_iot_svr.sh`
* `/etc/conf/medusa/xmpp_server_status.sh`

### nlp

* some program
* some files in `/install/root/etc/conf/nlp`
    * `host": "eis-nlp.dc-cn.cn.ecouser.net`
    * uses `libprotobuf` and a ton of libraries in `/instal/root/usr/lib/nlp`
    * unsure if used


### goahead web server on port 8888

* see `/etc/wifi/wd_hook.sh` and `/etc/rc.d/goahead.sh`
* `/etc/www/`
* hardcoded creds to a joshua
* script in `cgi-bin` called `startFct`, ELF binary
* `reqDo` another binary
* TODO what is this is it even running on boot?

### ROS

* ros melodic
* file path: `/opt/ros/melodic`
* https://wiki.ros.org/melodic
* ROS (Robot Operating System)
* ROS master on http://localhost:11311
* can be updated with OTA? `/etc/conf/dxai_ota.json` some sort of node
* DXAI = ROS config in `/etc/conf/`


### software nodes

* maybe part of medusa?
* seems to be part of "eros"
* or liberos
* `/usr/lib/node` has `.so` files
* config for each in `/etc/conf/`
* e.g. `/usr/lib/node/liberos_node_data_filter.so` and `/etc/conf/data_filter_node.json`
* node for OTA

### bumbee

part of medusa? responsible for wifi? ota?

`    #	mdsctl bumbee "{\"todo\":\"SetApConfig\",\"s\":\"${SSID}\",\"p\":\"${PASSPHRASE}\",\"sc\":\"${sc}\",\"sck2\":\"${sck2}\",\"lb\":\"${lb}\"}"`
`/etc/wifi/bumbee_hook.sh`

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

### netmon

* similar to medusa, a daemon that does wifi management
* has a ctl command `netmon_ctl` and socket `/tmp/netmon.sock`
* TODO `"server_file_path":"/data/config/netmon/serv.conf"`
* think stores wifi info there ^

### utils

* `/usr/bin/factory_fun` bash utils (in `/usr/bin` for some reason)
    * valuable source of info
* `netmon_ctl` communicates to netmon socket and sends json?
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

broken into plugins: `/usr/lib/medusa`

* has a lua library path: `/usr/lib/medusa/shell/lua`
    * TODO is it possible to inject some lua code that runs under the `medusa` thread?

* short names: `md`
* possible main config file: `/tmp/deebot_x3.conf`
* `mdsctl` to communicate to daemon, similar to `avacmd`
* socket: `/tmp/mds_cmd.sock`
* config? `/tmp/log/md.log`
* config files also in `/data/config/medusa/`
    * user DB? user ecovacs info?


possibly some config in `/dev/ubi2_0` with file offsets?
`			"joylink_tiot_parameters_offset":10240,`


example commands (from `/etc/conf/factory.conf`)
```json
{
    "sys_get":"mdsctl sys0 '{\"pid_get\":\"get_all\"}'",
    "wifi_test":"netmon_ctl -s /tmp/netmon.sock -j '{\"get\":\"online_dev_info\"}'",
    "time_get":"mdsctl time0 '{\"todo\":\"time\",\"cmd\":\"pull_time\"}'",
    "time_set":"mdsctl time0 '{\"todo\":\"time\",\"cmd\":\"set_time\",\"from\":\"net\",\"senconds\":-1,\"timezone\":\"+8\"}'",
    "spk_test":"mdsctl audio0 '{\"todo\":\"audio\",\"cmd\":\"play\",\"file\":\"/media/music/ZH/1\",\"baton\":1}'",
    "default_language_get":"mdsctl audio0 '{\"todo\":\"audio\",\"cmd\":\"get_language\"}'",
    "language_test":"mdsctl audio0 '{\"todo\":\"audio\",\"cmd\":\"play\",\"file\":\"null\",\"baton\":1}'",
    "default_country_get":"mdsctl sys0 '{\"todo\":\"sys\",\"cmd\":\"get_country\"}'"
}
```

some possible commands in `/etc/conf/func_table.conf`
```
"name":"ota",
"elem":["ota", "getOta","onOta","setOta"]
```
where `mdsctl fw {"todo":"getOta"}`

may be able to use `setOta` TODO


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


## mcu

* `/opt/mcu_sl.bin` ?
* exposed on `/dev/ttyS0`


## devices

* `/dev/ubi0_0` - rootfs
    * `ubi0_0.img: Squashfs filesystem, little endian, version 4.0, zlib compressed, 83176110 bytes, 4050 inodes, blocksize: 131072 bytes, created: Fri Nov 18 04:21:25 2022`
* `/dev/ubi1_0` - `/data`
    * `ubi1_0.img: UBIfs image, sequence number 32, length 4096, CRC 0x431d9397`
* `/dev/ubi2_0` - `SYSINFO` device 
  * `ubi2_0.img: ISO-8859 text, with very long lines (65536), with no line terminators`
  * `SYSINFO_DEV=/dev/ubi2_0` from `/usr/bin/factory_fun`
  * a lot of offsets used to pull data from this device
* `/dev/ubi3_0` - AI models
  * `ubi3_0.img: Squashfs filesystem, little endian, version 4.0, lz4 compressed, 71406437 bytes, 17 inodes, blocksize: 131072 bytes, created: Fri Nov 18 04:21:26 2022`
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

### SYSINFO

an example of updating device

`/etc/wifi/bumbee_hook.sh`

```
    ubi_leb_update_str /dev/ubi2_0 -i "{\"did\":\"${did}\",\"password\":\"${password}\",\"type\":\"${type}\",\"sc\":\"${sc}\",\"lb\":\"${lb}\"}" -n ${tiot_leb_num} -s $((${tiot_block_size}*${tiot_count})) --leb_offset=$((${tiot_block_size}*${tiot_offset}))
```

* `xxd -a -g 1 ubi2_0.img > ubi2_0.hexdump` to get some data in grepable format
* can see secret for mqtt and endpoint
* can also see in `/tmp/ls.json`, not sure what makes this file

to read on the device (from `post_boot.sh` variables from `/usr/bin/factory_fun`):
* `ubi_read ${SYSINFO_DEV} -f /tmp/config.bin -n ${LDS_LEB_NUM} -s $((${LDS_COUNT}*${BLOCK}))  --leb_offset=$((${LDS_OFFSET}*${BLOCK}))`


### rootfs

rootfs is `/dev/ubiblock0_0` and `squashfs`

found in kernel command-line parameters

```
bash-4.4# cat /proc/cmdline
earlycon kgdboc=ttyS0 console=ttyS0,115200 raid=noautodetect hobotboot.reson=POWER_RESET ubi.mtd=5 ubi.block=0,rootfs,4096 root=/dev/ubiblock0_0 rootfstype=squashfs ro rootwait mtdparts=hr_na
```

to unsquash run: `unsquashfs -d ubi0_0 ./ubi0_0.img`

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
