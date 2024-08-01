#!/usr/bin/env python3

import json
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
import math

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML(typ='rt')
yaml.explicit_start = True
yaml.default_flow_style = False
yaml.width = math.inf

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
class OutputMessages:
    p2p: dict = field(default_factory=dict)
    atr: dict = field(default_factory=dict)
    dtgcfg: dict = field(default_factory=dict)
    cfg: dict = field(default_factory=dict)
    unknown: list = field(default_factory=list)

@dataclass
class Output:
    subscriptions: list = field(default_factory=list)
    # messages: list = field(default_factory=list)
    messages: OutputMessages = field(default_factory=OutputMessages)

output = Output()

def get_msgs(f):
    for line in f:
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

p2p_requests = {} # request_id: {request: {}, response: {}}

def handle_publish(src, dst, msg):
    topic = msg['mqtt_mqtt_topic']
    topic_split = topic.split('/')
    prefix, topic_type, *_ = topic_split
    if prefix != 'iot':
        raise NotImplementedError()

    data = msg['mqtt_mqtt_msg_text']
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        pass
    match topic_type:
        case 'p2p':
            # iot/p2p/SetTime/HelperMQClientId-awsna-sts-ngiot-mqsjmq-38/ecosys/1234/did/1vxt52/resource/q/f4r0/j
            _, topic_type, cmd, broker, ecosys, ecosys_id, did, mid, resource, request_type, request_id, _ = topic_split
            if request_type == 'q':   # cloud -> robot
                if request_id in p2p_requests:
                    raise Exception()
                p2p_requests[request_id] = { 'request': { 'src': src, 'dst': dst, 'data': data, 'raw': msg } }
            elif request_type == 'p': # robot -> cloud
                if not request_id in p2p_requests:
                    raise Exception()
                p2p_requests[request_id]['response'] = { 'src': src, 'dst': dst, 'data': data, 'raw': msg }
            elif request_type == 'm':
                output.messages.unknown.append({ 'src': src, 'dst': dst, 'data': data, 'raw': msg })
                # unhandled
                return
            else:
                raise NotImplementedError()
        case 'atr':
            _, topic_type, cmd, did, mid, resource, _ = topic_split
            if not cmd in output.messages.atr:
                output.messages.atr[cmd] = []
            output.messages.atr[cmd].append({ 'src': src, 'dst': dst, 'data': data, 'raw': msg })
        case 'dtgcfg' | 'cfg':
            # lazy this is not true for cfg and dtgcfg
            _, topic_type, did, mid, resource, _, cmd = topic_split
            topic_type_output = getattr(output.messages, topic_type)
            if not cmd in topic_type_output:
                topic_type_output[cmd] = []
            topic_type_output[cmd].append({ 'src': src, 'dst': dst, 'data': data, 'raw': msg })
        case _:
            output.messages.unknown.append(msg)


def handle_msg(src, dst, msg):
    msg_type = MessageType(int(msg['mqtt_mqtt_msgtype']))
    match msg_type:
        # case MessageType.CONNECT:
        #     print(msg)
        case MessageType.SUBSCRIBE:
            output.subscriptions.append(msg['mqtt_mqtt_topic'])
        case MessageType.PUBLISH:
            handle_publish(src, dst, msg)

def main():
    for packet in get_msgs(sys.stdin):
        for msg in packet['msgs']:
            handle_msg(packet['src'], packet['dst'], msg)

    for r in p2p_requests:
        topic_split = p2p_requests[r]['request']['raw']['mqtt_mqtt_topic'].split('/')
        _, topic_type, cmd, broker, ecosys, ecosys_id, did, mid, resource, request_type, request_id, _ = topic_split
        if not cmd in output.messages.p2p:
            output.messages.p2p[cmd] = []
        output.messages.p2p[cmd].append(p2p_requests[r])

    d = asdict(output)
    yaml.dump(d, sys.stdout)

if __name__ == '__main__':
    sys.exit(main())
