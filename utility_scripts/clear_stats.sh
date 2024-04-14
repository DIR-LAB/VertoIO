#!/bin/bash

log_file=$1

lctl set_param llite.*.*stats=0 llite.*.extents_stats=1 |& tee -a $log_file
lctl set_param osc.*.*stats=0 |& tee -a $log_file
