#!/bin/sh

load() { dropbear; }
unload() { killall dropbear || true; }

case "$1" in
      start)
            load
             ;;
       stop)
            unload
             ;;
       restart)
            unload
            load
             ;;
        *)
             echo "$0 <start/stop/restart>"
             ;;
esac
