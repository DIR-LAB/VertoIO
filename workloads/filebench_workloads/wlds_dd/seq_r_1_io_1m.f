set $dir=/mnt/hasanfs/tmp22
set $filesize=10g
set $iosize=1m
set $nthreads=1
set $workingset=0
set $directio=0

define file name=largefile1,path=$dir,size=$filesize,prealloc,reuse,paralloc

define process name=wld_p,instances=1
{
  thread name=wld_t,memsize=5m,instances=1
  {
    flowop read name=readOP,filename=largefile1,iosize=$iosize,workingset=$workingset,directio=$directio
  }
}

echo "Random RW Version 3.0 personality successfully loaded"

create files
system "sync"
system "echo 3 > /proc/sys/vm/drop_caches"
system "lctl set_param ldlm.namespaces.*.lru_size=clear"

psrun 10 300
