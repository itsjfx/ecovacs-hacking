# notes for X1 Omni

<https://robotinfo.dev/detail_ecovacs.1vxt52_0.html>

## info on X1

* Horizon X3M SoC
* `Linux deboot 4.14.74 #1 SMP PREEMPT Sat Sep 3 10:54:50 CST 2022 aarch64 GNU/Linux`
* large use of linaro GNU toolchain for compiling tools like Python etc
    * seems to be done on dev machines (?)
* internal project name seems to be `px30-ai` or `AI_px30` (?)
* "platform" of the device seems to be an `x3`
* base distro unknown
* serial number gets dumped in bootup phase, as well as MQTT config and some secrets
* these are stored in the `SYSINFO` device (mentioned later), you can grab these values easily


## TASKS

* [x] gain root shell via uart
* [x] dump all file systems
    * [x] see [dumping files](#dumping-files)
* [x] rewrite the rootfs
* [x] write script to rewrite rootfs
    * [x] add dropbear for SSH
    * [x] add ssl cert from mitmproxy
    * [x] enable `autostart` init.d script so files from `/data/autostart` are loaded
* [x] extract data from [SYSINFO](#sysinfo)
* [x] get inspection working for HTTPS
* [x] get inspection working for MQTT
* [x] inspect files on file systems
    * [ ] rootfs (mostly done except for):
        * [ ] look at `/etc/init.d` scripts
        * [ ] look at medusa config
        * [ ] look at deebot config
    * [ ] data
    * [ ] models
    * [ ] recovery ?
* [ ] figure out how to do OTA properly
    * really tricky cause the robot I got has already been updated to the latest firmware
    * so I would probably have to fake the firmware version in SYSINFO and then trigger an OTA upgrade
    * to see exactly how it works
    * the main reason is I want to see how to do update the MCU and model files

* [ ] factory reset bot, and do a lot of net capturing of normal operations
* [ ] look at bumper, and then figure out how to write a custom cloud
    * write in node?
    * something that can be run on both the robot and a remote machine
    * [ ] TASKS
        * [ ] simple operations
            * [ ] start vacuum
            * [ ] stop vacuum
        * [ ] extract map

## gaining access

### how to get a root shell via UART

i was able to do it on updated firmware. YMMV.

* reverse the diagram 180 degrees given by Dennis
    * so gnd on the side closest to the micro usb
    * tx/rx on the other side
* plug in USB, connect, then switch on
    * i run `bin/uart` to connect
    * default baud of `115200`
* root password: <https://builder.dontvacuum.me/ecopassword.php>

### patching firmware / rootfs

* use `bin/patch-rootfs`
* give a key as an arg, e.g. `--dropbear ~/.ssh/id_ed25519.pub`
    * this does no validation and just copies this to `/root/.ssh/authorized_keys`, so double check this file
* then run the commands from `repack_rootfs.txt` to patch the file system with the `.mod` file
* example usage from me: `bash bin/patch-rootfs dd/ubi0_0.img --dropbear ~/.ssh/id_ed25519.pub --add-cert /a/ecovacs-hacking/secrets/mitmproxy-ca-cert.cer --keep`


```
➜ ~ ssh root@192.168.30.3 -J inspect
The authenticity of host '192.168.30.3 (<no hostip for proxy command>)' can't be established.
ED25519 key fingerprint is SHA256:HRwOmu4FpoAbVlnm1rr+HvEGEWi3B7Jx+3mSp/OnBZU.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '192.168.30.3' (ED25519) to the list of known hosts.
~ # whoami
root
~ # hostname
deboot
~ # cat patch.txt
patched 2024-07-03T12:09:33+00:00 with args: --dropbear /home/jfx/.ssh/id_ed25519.pub --add-cert /a/ecovacs-hacking/secrets/mitmproxy-ca-cert.cer --keep
~ # uname -a
Linux deboot 4.14.74 #1 SMP PREEMPT Sat Sep 3 10:54:50 CST 2022 aarch64 GNU/Linux
```

### why? (first try)

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

as rootfs is read-only, we need to flash it and install dropbear, and do some tweaks (maybe change login shell to bash or allow `/bin/sh`)

another option might be using an sshd which does not check `/etc/shells` or doing some `bubblewrap` but id rather just patch rootfs

## getting secrets

* `mdsctl bumbee "{"todo":"QueryIotInfo"}"` to get the mqtt important info
* `mdsctl sys0 '{"pid_get":"get_all"}'` to get serial numbers and password for an mqtt endpoint (unused?)


## traffic inspection

my setup is similar to: <https://github.com/bmartin5692/bumper/blob/master/docs/Sniffing.md>

* unifi AP network for inspect tagged with inspect vlan
* mikrotik router with inspect vlan setup, acting as dhcp server and pointing DNS & gateway to VM
* VM: running dnsmasq + mitmproxy transparent
* robot connected to inspect wifi
* my machine pulling netcap and `SSLKEYLOGFILE` from the VM and throwing it into wireshark

* I inject the mitmproxy cert to `/etc/certs/ssl/`, but this doesn't seem to be needed, as the client on the robot doesn't seem to check certificates
* It seems the MQTT endpoint is using a self-signed TLS cert, so `mitmproxy` was complaining. I had to add `--ssl-insecure` to fix it.
* MQTT is also on port 443 which is annoying cause Wireguard doesn't pick it up. after decoding one message as MQTT it figures it out

### wireshark

* edit -> preferences -> protocols -> TLS
    * RSA keys list, add `mitmproxy-ca.pem`
    * set Pre-Master-Secret log filename

## networking

### hosts

maybe relevant: <https://github.com/bmartin5692/bumper/blob/master/docs/Sniffing.md>

actual hosts:
* a lot of calls to `api-rapp.cn.ecouser.net` to get baidu data
* and main endpoint is `jmq-ngiot-au.area.ww.ecouser.net`

unsure if used:
* `lb.ecouser.net`
* `mq.ecouser.net`
* `portal.ecouser.net`
* `portal-ww.ecouser.net`

## services (socket files)

(from `factory.conf`)
* "unix_wifi_server":"/tmp/netmon.sock"
* "unix_medusa_server":"/tmp/mds_cmd.sock"

## listening services (ports)

dropbear is from me :)
```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:11311         0.0.0.0:*               LISTEN      2493/python
tcp        0      0 127.0.0.1:54543         0.0.0.0:*               LISTEN      2367/medusa
tcp        0      0 127.0.0.1:8081          0.0.0.0:*               LISTEN      2279/audioDaemon
tcp        0      0 127.0.0.1:34003         0.0.0.0:*               LISTEN      2367/medusa
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      2429/dropbear
tcp        0      0 127.0.0.1:44025         0.0.0.0:*               LISTEN      2372/deebot
tcp        0      0 127.0.0.1:50489         0.0.0.0:*               LISTEN      2372/deebot
tcp        0      0 127.0.0.1:58779         0.0.0.0:*               LISTEN      2622/speech_inter_c
tcp        0      0 127.0.0.1:42427         0.0.0.0:*               LISTEN      2377/deebot
tcp        0      0 127.0.0.1:2012          0.0.0.0:*               LISTEN      2367/medusa
tcp        0      0 127.0.0.1:45157         0.0.0.0:*               LISTEN      2350/python
tcp        0      0 127.0.0.1:41099         0.0.0.0:*               LISTEN      2622/speech_inter_c
tcp        0      0 127.0.0.1:60461         0.0.0.0:*               LISTEN      2377/deebot
udp        0      0 127.0.0.1:59901         0.0.0.0:*                           2367/medusa
udp        0      0 0.0.0.0:67              0.0.0.0:*                           2950/dnsmasq
udp        0      0 127.0.0.1:33560         0.0.0.0:*                           2372/deebot
udp        0      0 0.0.0.0:15678           0.0.0.0:*                           2372/deebot
udp        0      0 0.0.0.0:15678           0.0.0.0:*                           2377/deebot
udp        0      0 0.0.0.0:2375            0.0.0.0:*                           2367/medusa
udp        0      0 127.0.0.1:37222         0.0.0.0:*                           2377/deebot
udp        0      0 127.0.0.1:33182         0.0.0.0:*                           2622/speech_inter_c
```

* `audio_daemon`
    * port 8081
    * `/etc/conf/audio_daemon.conf`
```
"unixSockPath":         "/tmp/audio_daemon.sock",
"ipaddr":               "127.0.0.1",
"port":                 8081,
```
* `ROS` master = http://localhost:11311
    * `/tmp/log/roslog`


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
  * example of sending messages to MCU (commented out, may not work)
  * `#echo -en '\x60\x53\x41\x00\x11\xc2\x44\x69\x43\x49\x02\xac\x0a' > /dev/ttyS1  #inform muc to reboot`

### SYSINFO

an example of updating device

`/etc/wifi/bumbee_hook.sh`

```bash
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



## file system

### interesting files

* `/usr/bin/upload_log.sh` serial number
* grep for `/home/` can see usernames in makefiles, as well as repo path and name


### mtd partitions


from recovery:
```
/tmp/backup # cat /proc/mtd
dev:    size   erasesize  name
mtd0: 00500000 00040000 "bootloader"
mtd1: 00380000 00040000 "uboot"
mtd2: 00500000 00040000 "sys"
mtd3: 00f00000 00040000 "boot"
mtd4: 00f00000 00040000 "boot_b"
mtd5: 06e00000 00040000 "system"
mtd6: 01e00000 00040000 "system_b"
mtd7: 09600000 00040000 "model"
mtd8: 0b280000 00040000 "userdata"
mtd9: 00925000 0003e000 "rootfs"
mtd10: 0a244000 0003e000 "userdata"
mtd11: 0022e000 0003e000 "sys"
mtd12: 0441a000 0003e000 "model"
mtd13: 04f53000 0003e000 "rootfs"
```

post recovery:
```
~ # cat /proc/mtd
dev:    size   erasesize  name
mtd0: 00500000 00040000 "bootloader"
mtd1: 00380000 00040000 "uboot"
mtd2: 00500000 00040000 "sys"
mtd3: 00f00000 00040000 "boot"
mtd4: 00f00000 00040000 "boot_b"
mtd5: 06e00000 00040000 "system"
mtd6: 01e00000 00040000 "system_b"
mtd7: 09600000 00040000 "model"
mtd8: 0b280000 00040000 "userdata"
mtd9: 05004000 0003e000 "rootfs"
mtd10: 0a244000 0003e000 "userdata"
mtd11: 0022e000 0003e000 "sys"
mtd12: 0441a000 0003e000 "model"
```


### df -h

```
~ # df -h
Filesystem                Size      Used Available Use% Mounted on
/dev/root                80.1M     80.1M         0 100% /
devtmpfs                334.9M         0    334.9M   0% /dev
tmpfs                   493.4M      2.8M    490.6M   1% /tmp
run                     493.4M     80.0K    493.3M   0% /run
none                    493.4M     16.0K    493.3M   0% /dev/shm
/dev/ubi1_0             148.9M      9.8M    139.1M   7% /data
/dev/ubiblock3_0         68.1M     68.1M         0 100% /model
```

### mount

```
~ # mount
/dev/root on / type squashfs (ro,relatime)
devtmpfs on /dev type devtmpfs (rw,relatime,size=342896k,nr_inodes=85724,mode=755)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /tmp type tmpfs (rw,nodev,relatime)
run on /run type tmpfs (rw,nodev,relatime)
none on /dev/shm type tmpfs (rw,nosuid,nodev,relatime)
none on /dev/pts type devpts (rw,relatime,mode=600,ptmxmode=000)
/dev/ubi1_0 on /data type ubifs (rw,sync,relatime,bulk_read,ubi=1,vol=0)
/dev/ubiblock3_0 on /model type squashfs (ro,relatime)
pstore on /mnt type pstore (rw,relatime)
```

### directories (draft)

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


## map

`/data/MapFiles` TODO

## software

### OTA

* this ran after factory reset
    * `GET https://portal-ww.ecouser.net/api/ota/products/wukong/class/1vxt52/firmware/latest.json?sn=x&ver=2.3.9&mac=x&plat=QJ2077&module=fw0 HTTP/1.1`
    * UA: `wget`, some script
    * this works `curl 'https://portal-ww.ecouser.net/api/ota/products/wukong/class/1vxt52/firmware/latest.json?sn=x&ver=1.8.7&mac=x&plat=QJ2077&module=fw0'`
        * gives a bin file
* in some log files, OTA for AI models?
    * `/data/log/models_update.log`
    * `https://portal-ww.ecouser.net:443/api/ota/products/wukong/class/1vxt52/firmware/latest.json?sn=x&ver=2.3.9&mac=x&plat=QJ2077&module=AIConfig`
        * note `module=AIConfig`

### internal python packages

* a bunch of weird internal python packages with auto-generated code
* unsure if anything on the bot uses them
* e.g. `/usr/lib/python2.7/site-packages/ota`

### MQTT

* real endpoint is `jmq-ngiot-au.area.ww.ecouser.net` on `443` !
    * this is set in `/data/config/medusa/rwCfg.json`
    * i'm unsure what happens if factory reset occurs, how does it know AU? where does it default to?
* medusa is responsible for MQTT
```
~ # netstat -anp | grep 443
tcp        0      0 192.168.30.3:51170      18.144.160.2:443        ESTABLISHED 2383/medusa
```
* `mq-ww.ecouser.net` (NOT SURE IF USED)

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


### deebot / EROS

* seems to be the main software alongside `medusa`
* `/etc/rc.d/deebot.sh`
* i believe it runs ROS, calls itself "EROS" (?), perhaps it wraps it?
    * `/etc/conf/dxai_node.json` is fed into the `deebot` binary

#### EROS software nodes/libaries

* liberos = eros library files
* `/usr/lib/node` has `.so` files
* config for each in `/etc/conf/`
* e.g. `/usr/lib/node/liberos_node_data_filter.so` and `/etc/conf/data_filter_node.json`
* node for OTA

### bumbee

part of medusa? responsible for wifi? ota?

from `/etc/wifi/bumbee_hook.sh`:
* `mdsctl bumbee "{\"todo\":\"SetApConfig\",\"s\":\"${SSID}\",\"p\":\"${PASSPHRASE}\",\"sc\":\"${sc}\",\"sck2\":\"${sck2}\",\"lb\":\"${lb}\"}"`

### cjp

`cjp` seems like a JSON parser, similar to `jq`

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
    * `FW_FILE=/data/fw.bin`
    * mcu update?
```bash
mdsctl rosnode '{"todo":"mcuota","type":3,"act":"start"}'
mdsctl rosnode '{"todo":"mcuota","type":0,"act":"start"}'
sleep 1.5
mdsctl "mcuota" '{"todo": "fw_mcu", "cmd": "mcu_upgrade_start", "file_path":"/tmp/mcu.bin"}'
```

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

it may be easiest to `tar` `/tmp` and `/data`

as it has curl, you can also use:
* `bin/www` which is running python
* or <https://github.com/Hypfer/valetudo-helper-httpbridge>


## mcu

* `/opt/mcu_sl.bin` ?
* exposed on `/dev/ttyS0`


## cron

TODO

`/usr/bin/autoOTA.sh`
