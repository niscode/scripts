#!/bin/sh

OUTPUT_DEVICE=`pactl list short sinks | grep Yamaha | awk '{print $2}'`
echo $OUTPUT_DEVICE
pactl set-default-sink $OUTPUT_DEVICE