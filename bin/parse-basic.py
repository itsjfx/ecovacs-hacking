#!/usr/bin/env python3

import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML(typ='rt')
yaml.explicit_start = True
yaml.default_flow_style = False

class MessageType(Enum):
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14

@dataclass
class Output:
    subscriptions: list = field(default_factory=list)
    messages: list = field(default_factory=list)

file = sys.stdin
output = Output()

def get_msgs():
    for line in file:
        data = json.loads(line)
        if 'index' in data:
            continue
        if not 'mqtt' in data['layers']:
            continue

        msgs = data['layers']['mqtt']
        if not isinstance(msgs, list):
            msgs = [msgs]

        yield {
            'src': data['layers']['ip']['ip_ip_src'],
            'dst': data['layers']['ip']['ip_ip_dst'],
            'msgs': msgs,
        }
        # yield from msgs

def handle_msg(msg):
    msg_type = MessageType(int(msg['mqtt_mqtt_msgtype']))
    match msg_type:
        # case MessageType.CONNECT:
        #     print(msg)
        case MessageType.SUBSCRIBE:
            output.subscriptions.append(msg['mqtt_mqtt_topic'])
        case MessageType.PUBLISH:
            data = msg['mqtt_mqtt_msg_text']
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass
            output.messages.append({'topic': msg['mqtt_mqtt_topic'], 'data': data})

def main():
    for msg in get_msgs():
        for msg in msg['msgs']:
            handle_msg(msg)

    d = asdict(output)
    yaml.dump(d, sys.stdout)

if __name__ == '__main__':
    sys.exit(main())
