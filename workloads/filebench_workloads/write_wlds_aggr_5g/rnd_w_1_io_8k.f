set $dir=/mnt/hasanfs/tmp2
set $filesize=5g
set $iosize=8k
set $nthreads=1
set $workingset=0
set $directio=0

define file name=largefile1,path=$dir,size=$filesize,prealloc,reuse,paralloc

define process name=wld_p,instances=1
{
  thread name=wld_t,memsize=5m,instances=1
  {
    flowop write name=writeOP,filename=largefile1,iosize=$iosize,random,workingset=$workingset,directio=$directio
  }
}

echo "Random RW Version 3.0 personality successfully loaded"

create files
system "sync"
system "echo 3 > /proc/sys/vm/drop_caches"
system "lctl set_param ldlm.namespaces.*.lru_size=clear"

psrun 10 300
