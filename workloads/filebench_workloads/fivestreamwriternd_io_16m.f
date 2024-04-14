#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#
#
# Copyright 2007 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

set $dir=/mnt/hasanfs/tmp3
set $filesize=10g
set $nthreads=1
set $iosize=16m

define file name=largefile1,path=$dir,size=$filesize,prealloc,reuse
define file name=largefile2,path=$dir,size=$filesize,prealloc,reuse
define file name=largefile3,path=$dir,size=$filesize,prealloc,reuse
define file name=largefile4,path=$dir,size=$filesize,prealloc,reuse
define file name=largefile5,path=$dir,size=$filesize,prealloc,reuse

define process name=wld_p,instances=1
{
  thread name=wld_t1,memsize=80m,instances=$nthreads
  {
    flowop write name=writeOP1,filename=largefile1,iosize=$iosize,random
  }
  thread name=wld_t2,memsize=80m,instances=$nthreads
  {
    flowop write name=writeOP2,filename=largefile2,iosize=$iosize,random
  }
  thread name=wld_t3,memsize=80m,instances=$nthreads
  {
    flowop write name=writeOP3,filename=largefile3,iosize=$iosize,random
  }
  thread name=wld_t4,memsize=80m,instances=$nthreads
  {
    flowop write name=writeOP4,filename=largefile4,iosize=$iosize,random
  }
  thread name=wld_t5,memsize=80m,instances=$nthreads
  {
    flowop write name=writeOP5,filename=largefile5,iosize=$iosize,random
  }
}

echo  "Five Stream Write Version 3.0 personality successfully loaded"

create files
system "sync"
system "echo 3 > /proc/sys/vm/drop_caches"
system "lctl set_param ldlm.namespaces.*.lru_size=clear"

psrun 10 300

