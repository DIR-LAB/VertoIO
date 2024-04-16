#!/bin/bash

#mpi_cmd="mpirun -np 1 -env LD_PRELOAD /root/localssd/spack/opt/spack/linux-centos7-haswell/gcc-13.2.0/darshan-runtime-3.4.4-b6vinc3onfian5ghb6kxbgf7v3ymmtbi/lib/libdarshan.so -env DARSHAN_CONFIG_PATH /root/darshan_config  -env DARSHAN_ENABLE_NONMPI 1 -env DARSHAN_LOGPATH /root/localssd/dlio_tests/rpc_tuning_tests/bert_v100_custom_dflt"
mpi_cmd="mpirun -np 1"
CUSTOM_CONFIG_FOLDER="/root/localssd/dlio_tests"
custom_workload="bert_v100_custom"

$mpi_cmd dlio_benchmark --config-dir $CUSTOM_CONFIG_FOLDER workload=$custom_workload