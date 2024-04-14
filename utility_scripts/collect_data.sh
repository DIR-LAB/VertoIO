#!/bin/bash

log_file=$1

lctl get_param llite.*.max_* llite.*.*stats |& tee -a $log_file
lctl get_param osc.*.cur_* osc.*.import osc.*.max_* osc.*.*stats |& tee -a $log_file
