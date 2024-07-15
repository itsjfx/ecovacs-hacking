# Cloud Reversing

## tshark

```
tshark -r /path/to/file.pcap -o tls.keylog_file:/a/ecovacs-hacking/secrets/sslkeylogfile.txt -d tls.port==443,mqtt
```

* `tshark` output is not that helpful as is cause it doesn't decode `mqtt` payloads, so you have to write that stuff yourself based on the JSON output
* but all the information is there
* or to show msgs with data (probably publish ones)
  * `tshark -r /tmp/thing.pcap -o tls.keylog_file:/a/ecovacs-hacking/secrets/sslkeylogfile.txt -d tcp.port==55868,mqtt -T json | jq -r '.[]._source.layers.mqtt | if .["mqtt.msg"] != null then . else empty end'`

## mqttshark

use <https://github.com/itsjfx/mqttshark>

```
./mqttshark -r /tmp/thing.pcap -o tls.keylog_file:/a/ecovacs-hacking/secrets/sslkeylogfile.txt -d tls.port==443,mqtt --truncate-clientid=900 --truncate-payload=900 --truncate-topic=900
```

* this is an easily parsable format, can do `sed` and such: `sed 's/.*payload="//; s/"$//'`

## wireshark

From server:
```
ip.src == 18.144.160.2 and mqtt and _ws.col.info != "Ping Response"
```

From robot:
```
ip.src == 192.168.30.3 and mqtt and _ws.col.info != "Ping Request"
```

## Glossary (message types)


* topics: <https://github.com/DeebotUniverse/client.py/blob/33bc36b494a0fd7e3cebc917da0f3bc24006007b/deebot_client/mqtt_client.py#L38-L50>
* header: <https://github.com/DeebotUniverse/client.py/blob/33bc36b494a0fd7e3cebc917da0f3bc24006007b/deebot_client/commands/json/common.py#L40-L48>
* message format: <https://github.com/DeebotUniverse/client.py/blob/33bc36b494a0fd7e3cebc917da0f3bc24006007b/deebot_client/mqtt_client.py#L315C13-L315C23>

* `TYPE` - either `p2p` or `atr`
    * my guess is `p2p` are device prompted messages/sending data to device directly = robot <-> device
    * `atr` may be for cloud device state, and may not be as important = robot <-> cloud server
* Secret values are [documented here](./x1_omni.md#secrets)

### dtgcfg

* request from cloud to robot
    * `iot/dtgcfg/${MID}/${DID}/${RESOURCE}/j/MQACL`

### atr message

* request from robot to cloud (1 way?)
    * `iot/atr/${CMD}/${DID}/${MID}/${RESOURCE}/j`

### p2p message

* req: request to robot (from cloud) `q`
    * topic format: `iot/${TYPE}/${MSG}/HelperMQClientId-awsna-sts-ngiot-mqsjmp-ID/ecosys/1234/${DID}/${MID}/${RESOURCE}/q/${REQUEST_ID}/j`
* res: response from robot (to cloud) `p`
    * topic format: `iot/${TYPE}/${MG}/${DID}/${MID}/${RESOURCE}/HelperMQClientId-awsna-sts-ngiot-mqsjmp-ID/ecosys/1234/p/${REQUEST_ID}/j`

### cfg message

* request from cloud to robot
    * `iot/cfg/${DID}/${MID}/${RESOURCE}/j/setting2`




## Message Examples (TODO, delete this and automate this, done manually)


### cfg

#### setting2

```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 138
    Topic Length: 67
    Topic: iot/cfg/***REMOVED***/***REMOVED***/***REMOVED***/j/setting2
    Message: {"setting2":{"cfg":{"improve":{"version":"11.16","isAccept":false}}}}
```


### dtgcfg

#### MQACL

```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 2423
    Topic Length: 67
    Topic: iot/dtgcfg/${MID}/${DID}/${RESOURCE}/j/MQACL
    Message : {"rcpRules":{"defaultACL":"drop","luaScript":"RUNPTElCPXJlcXVpcmUoImVjb2xpYi9lY29saWIiKWxhc3RQYXNzZWRQYXlsb2FkPXt9ZnVuY3Rpb24gR2V0TFBQZChhLGIpaWYgYT09RUNPTElCLkVudW1SY3BUeXBlLnJlcG9ydCBhbmQgbGFzdFBhc3NlZFBheWxvYWRbYl1+PW5pbCB0aGVuIHJldHVybiBsYXN0UGFzc2VkUGF5bG9hZFtiXS52YWwsbGFzdFBhc3NlZFBheWxvYWRbYl0udHMgZW5kO3JldHVybiBuaWwsbmlsIGVuZDtmdW5jdGlvbiBNcXR0UGFzc2VkKGMpbG9jYWwgZD1FQ09MSUIuUGFyc2VUb3BpYyhjLnRvcGljKWlmIGQucmNwVHlwZT09RUNPTElCLkVudW1SY3BUeXBlLnJlcG9ydCB0aGVuIGxhc3RQYXNzZWRQYXlsb2FkW2QucmNwTmFtZV09e31sYXN0UGFzc2VkUGF5bG9hZFtkLnJjcE5hbWVdLnZhbD1jLnBheWxvYWQ7bGFzdFBhc3NlZFBheWxvYWRbZC5yY3BOYW1lXS50cz1vcy50aW1lKCllbmQgZW5kO2Z1bmN0aW9uIE1xdHRBY2woYylsb2NhbCBlPWZhbHNlO2ZvciBmLGcgaW4gcGFpcnMoe30pZG8gaWYgYy5leHRyYUluZm8uZndWZXI9PWcgdGhlbiBlPXRydWU7YnJlYWsgZW5kIGVuZDtpZiBub3QgZSB0aGVuIGMuY2Ioe3Bhc3M9ZmFsc2UsdXNlckRhdGE9Yy51c2VyRGF0YX0pcmV0dXJuIGVuZDtpZiB0eXBlKG1haW4pfj0iZnVuY3Rpb24idGhlbiBjLmNiKHtwYXNzPXRydWUsdG9waWM9Yy50b3BpYyxwYXlsb2FkPWMucGF5bG9hZCxxb3M9Yy5xb3MscmV0YWluPWMucmV0YWluLHVzZXJEYXRhPWMudXNlckRhdGF9KXJldHVybiBlbmQ7bG9jYWwgaD1FQ09MSUIuUGFyc2VDbGllbnRJRChjLmNsaWVudElEKWxvY2FsIGQ9RUNPTElCLlBhcnNlVG9waWMoYy50b3BpYylpZiBoPT1uaWwgb3IgZD09bmlsIHRoZW4gYy5jYih7cGFzcz10cnVlLHRvcGljPWMudG9waWMscGF5bG9hZD1jLnBheWxvYWQscW9zPWMucW9zLHJldGFpbj1jLnJldGFpbix1c2VyRGF0YT1jLnVzZXJEYXRhfSlyZXR1cm4gZW5kO2xvY2FsIGksajtpLGo9R2V0TFBQZChkLnJjcFR5cGUsZC5yY3BOYW1lKW1haW4oe2V4dHJhSW5mbz1jLmV4dHJhSW5mbyxuYW1lPWMudXNlcm5hbWUsZGlkPWguZGlkLG1pZD1oLnR5cGVJRCxyZXNvdXJjZT1oLnJlc291cmNlLHJjcE5hbWU9ZC5yY3BOYW1lLHJjcFR5cGU9ZC5yY3BUeXBlLHRvRGlkPWQudG9ESUQsdG9NaWQ9ZC50b1R5cGVJRCx0b1Jlc291cmNlPWQudG9SZXNvdXJjZSxwYXlsb2FkVHlwZT1kLnBheWxvYWRUeXBlLHBheWxvYWQ9Yy5wYXlsb2FkLGxhc3RQYXNzZWRQYXlsb2FkPWksbGFzdFBhc3NlZFBheWxvYWRUUz1qfSxmdW5jdGlvbihrLGwpaWYgayB0aGVuIGMuY2Ioe3Bhc3M9dHJ1ZSx0b3BpYz1jLnRvcGljLHBheWxvYWQ9bCxxb3M9Yy5xb3MscmV0YWluPWMucmV0YWluLHVzZXJEYXRhPWMudXNlckRhdGF9KWVsc2UgYy5jYih7cGFzcz1mYWxzZSx1c2VyRGF0YT1jLnVzZXJEYXRhfSllbmQgZW5kKWVuZAo=","out":[{"topic":"iot/atr/onSimpleARMapSet/+/+/+/+","minInterval":0},{"topic":"iot/atr/onError/+/+/+/+","minInterval":0},{"topic":"iot/atr/onEvt/+/+/+/+","minInterval":0},{"topic":"iot/atr/CleanResult/+/+/+/+","minInterval":0},{"topic":"iot/atr/OfflineMap/+/+/+/+","minInterval":0},{"topic":"iot/atr/cruiseJPEG/+/+/+/+","minInterval":0},{"topic":"iot/atr/smartSpeakerTransaction/+/+/+/+","minInterval":0}]}}{"rcpRules":{"defaultACL":"drop","luaScript":"RUNPTElCPXJlcXVpcmUoImVjb2xpYi9lY29saWIiKWxhc3RQYXNzZWRQYXlsb2FkPXt9ZnVuY3Rpb24gR2V0TFBQZChhLGIpaWYgYT09RUNPTElCLkVudW1SY3BUeXBlLnJlcG9ydCBhbmQgbGFzdFBhc3NlZFBheWxvYWRbYl1+
```

#### setting2

```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 185
    Topic Length: 70
    Topic: iot/dtgcfg/${MID}/${DID}/${RESOURCE}/j/setting2
    Message: {"setting2":{"cfg":{"video":{"version":"13.01","isAccept":true},"improve":{"version":"11.15","isAccept":false}}}}

MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 138
    Topic Length: 67
    Topic: iot/cfg/${DID}/${MID}/${RESOURCE}/j/setting2
    Message: {"setting2":{"cfg":{"improve":{"version":"11.16","isAccept":false}}}}
```



### atr

#### onFwBuryPoint-bd_sysinfo

```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 3193
    Topic Length: 83
    Topic: iot/atr/onFwBuryPoint-bd_sysinfo/${DID}/${MID}/${RESOURCE}/j
    Message: {"header":{"pri":1,"tzm":600,"ts":"1720175340014","ver":"0.0.1","fwVer":"2.3.9","hwVer":"0.1.1","wkVer":"0.1.54"},"body":[{"signal":-51,"uptime":" 10:14:59 up 30 min,  0 users,  load average: 2.82, 2.60, 2.21, POWER_RESET","meminfo":"488356,522044","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:15:59 up 31 min,  0 users,  load average: 3.04, 2.67, 2.26, POWER_RESET","meminfo":"488116,522284","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:16:59 up 32 min,  0 users,  load average: 2.83, 2.70, 2.30, POWER_RESET","meminfo":"488072,522328","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:17:59 up 33 min,  0 users,  load average: 2.92, 2.75, 2.34, POWER_RESET","meminfo":"487764,522636","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:18:59 up 34 min,  0 users,  load average: 2.36, 2.65, 2.34, POWER_RESET","meminfo":"487840,522560","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:19:59 up 35 min,  0 users,  load average: 2.88, 2.72, 2.38, POWER_RESET","meminfo":"487652,522748","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:20:59 up 36 min,  0 users,  load average: 2.74, 2.70, 2.39, POWER_RESET","meminfo":"487984,522416","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:21:59 up 37 min,  0 users,  load average: 2.35, 2.60, 2.37, POWER_RESET","meminfo":"487588,522812","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:22:59 up 38 min,  0 users,  load average: 2.10, 2.47, 2.34, POWER_RESET","meminfo":"488280,522120","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:23:59 up 39 min,  0 users,  load average: 2.53, 2.53, 2.37, POWER_RESET","meminfo":"487496,522904","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:24:59 up 40 min,  0 users,  load average: 2.21, 2.45, 2.35, POWER_RESET","meminfo":"488116,522284","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:25:59 up 41 min,  0 users,  load average: 2.40, 2.45, 2.36, POWER_RESET","meminfo":"488400,522000","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:26:59 up 42 min,  0 users,  load average: 2.36, 2.42, 2.35, POWER_RESET","meminfo":"487780,522620","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:27:59 up 43 min,  0 users,  load average: 2.31, 2.41, 2.36, POWER_RESET","meminfo":"487688,522712","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"},{"signal":-51,"uptime":" 10:28:59 up 44 min,  0 users,  load average: 2.17, 2.34, 2.34, POWER_RESET","meminfo":"487968,522432","pos":"-80,-638","isvalid":1,"mapid":"0213306107","ts":"1720175339969"}]}
```



### p2p

#### Set Time

req:
```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 171
    Topic Length: 128
    Topic: iot/p2p/SetTime/HelperMQClientId-awsna-sts-ngiot-mqsjmq-14/ecosys/1234/${DID}/${MID}/${RESOURCE}/q/PFFE/j
    Message: {"ts":1720185645692,"tsInSec":1720185645}
```

res:
```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 142
    Topic Length: 128
    Topic: iot/p2p/SetTime/${DID}/${MID}/${RESOURCE}/HelperMQClientId-awsna-sts-ngiot-mqsjmq-14/ecosys/1234/p/PFFE/j
    Message: {"ret":"ok"}
```

#### Get Info

req:
```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 267
    Topic Length: 128
    Topic: iot/p2p/getInfo/HelperMQClientId-awsna-sts-ngiot-mqsjmq-19/ecosys/1234/a/b/c/q/d/j
    Message: {"body":{"data":["getMapState","getChargeState","getSleep","getError"]},"header":{"pri":2,"ts":"1720174485407","tzm":600,"ver":"0.0.22"}}
```

res:
```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 524
    Topic Length: 128
    Topic: iot/p2p/getInfo/a/b/c/HelperMQClientId-awsna-sts-ngiot-mqsjmq-19/ecosys/1234/p/d/j
    Message: {"header":{"pri":1,"tzm":600,"ts":"1720174484969","ver":"0.0.1","fwVer":"2.3.9","hwVer":"0.1.1","wkVer":"0.1.54"},"body":{"code":0,"msg":"ok","data":{"getMapState":{"data":{"state":"built"},"code":0,"msg":"ok"},"getChargeState":{"code":0,"msg":"ok","data":{"isCharging":1,"mode":"slot"}},"getSleep":{"code":0,"msg":"ok","data":{"enable":0}},"getError":{"code":0,"msg":"","data":{"code":[0]}}}}}
```

#### Go to dock

req:
```
MQ Telemetry Transport Protocol, Publish Message
    Header Flags: 0x30, Message Type: Publish Message, QoS Level: At most once delivery (Fire and Forget)
    Msg Len: 278
    Topic Length: 127
    Topic: iot/p2p/charge/HelperMQClientId-awsna-sts-ngiot-mqsjmq-14/ecosys/1234/a/b/c/q/d/j
    Message: {"body":{"data":{"act":"go","id":"1720172767480475","bdTaskID":"1720172767481986"}},"header":{"pri":2,"ts":"1720172767481","tzm":600,"ver":"0.0.22"}}
```
