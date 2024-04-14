#!/bin/bash

for cid in 110426 110401 111001 110412 110417 110408
# for cid in 110903
do
    # scp -r mrashid2@c220g5-$cid.wisc.cloudlab.us:/root/localssd/filebench/rpc_tuning_tests/* /Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/capes_tests/capes_run
    machine_dir=/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/capes_tests/capes_run/c220g5-$cid
    mkdir -p $machine_dir
    scp -r mrashid2@c220g5-$cid.wisc.cloudlab.us:/root/localssd/log/* $machine_dir
done