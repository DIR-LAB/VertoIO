#!/bin/bash

xfer_src="/Users/mrashid2/Adaptive-Tuning/exprmnt_excn_scripts/rolling_window_expr_scripts"
xfer_dst="/root/localssd/filebench"

for cid in 110426 110401 111001 110412 110417 110408
do
    scp -r "${xfer_src}"/xgb-models/* mrashid2@c220g5-$cid.wisc.cloudlab.us:"${xfer_dst}"
    scp -r "${xfer_src}"/tuning_scripts/* mrashid2@c220g5-$cid.wisc.cloudlab.us:"${xfer_dst}"
    scp -r "${xfer_src}"/common_data_relevant/* mrashid2@c220g5-$cid.wisc.cloudlab.us:"${xfer_dst}"
    scp -r "${xfer_src}"/filebench_workloads* mrashid2@c220g5-$cid.wisc.cloudlab.us:"${xfer_dst}"
done