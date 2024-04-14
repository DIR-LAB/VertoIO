#!/bin/bash

# configure MDS and MGS
# *** Change: ssh address, network interface (i.e. p1p1) ***
ssh -tt -p 22 mrashid2@c220g5-110403.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
mkfs.lustre --mgs --reformat /dev/sda5
mkfs.lustre --fsname=hasanfs --mgsnode=10.10.1.1@tcp --mdt --index=0 --reformat /dev/sda6
mkdir /mnt/mgt /mnt/mdt
mount -t lustre /dev/sda5 /mnt/mgt
mount -t lustre /dev/sda6 /mnt/mdt
exit
exit
EOF

# configure OSS
# *** Change: ssh address, network interface (i.e. p1p1) ***
ssh -tt -p 22 mrashid2@c220g5-110424.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=0 --reformat /dev/sda5
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=1 --reformat /dev/sda6
mkdir /mnt/ost0 /mnt/ost1
mount -t lustre /dev/sda5 /mnt/ost0
mount -t lustre /dev/sda6 /mnt/ost1
exit
exit
EOF

# *** Change: ssh address, network interface (i.e. p1p1) ***
ssh -tt -p 22 mrashid2@c220g5-110428.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=2 --reformat /dev/sda5
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=3 --reformat /dev/sda6
mkdir /mnt/ost2 /mnt/ost3
mount -t lustre /dev/sda5 /mnt/ost2
mount -t lustre /dev/sda6 /mnt/ost3
exit
exit
EOF

# *** Change: ssh address, network interface (i.e. p1p1) ***
ssh -tt -p 22 mrashid2@c220g5-110406.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=4 --reformat /dev/sda5
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=5 --reformat /dev/sda6
mkdir /mnt/ost4 /mnt/ost5
mount -t lustre /dev/sda5 /mnt/ost4
mount -t lustre /dev/sda6 /mnt/ost5
exit
exit
EOF

# *** Change: ssh address, network interface (i.e. p1p1) ***
ssh -tt -p 22 mrashid2@c220g5-110425.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=6 --reformat /dev/sda5
mkfs.lustre --fsname=hasanfs --ost --mgsnode=10.10.1.1@tcp --index=7 --reformat /dev/sda6
mkdir /mnt/ost6 /mnt/ost7
mount -t lustre /dev/sda5 /mnt/ost6
mount -t lustre /dev/sda6 /mnt/ost7
exit
exit
EOF


# ssh fingerprint check for client
# *** Change: ssh address, network interface (i.e. p1p1) ***
for cid in 110426 110401 110412 110417 110408
do
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f1)" > /etc/modprobe.d/lustre.conf
exit
exit
EOF
done

for cid in 111001
do
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us << EOF
sudo su -
echo "options lnet networks=tcp(enp94s0f0)" > /etc/modprobe.d/lustre.conf
exit
exit
EOF
done


# configure client
# *** Change: ssh address ***
for cid in 110426 110401 111001 110412 110417 110408
do
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us << EOF
sudo su -
mkdir /mnt/hasanfs/
mount -t lustre 10.10.1.1@tcp:/hasanfs /mnt/hasanfs/
yum -y install openmpi-devel tree tmux && echo "export PATH=/usr/lib64/openmpi/bin:$PATH
export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib
module purge
module load mpi/openmpi-x86_64" >> /root/.bashrc && source /root/.bashrc

mkdir keys
chown mrashid2 keys
cat /root/.ssh/id_rsa.pub >> /root/keys/pub_key.txt
exit
exit
EOF
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us cat /root/keys/pub_key.txt >> all.txt
done
cat all.txt

# *** Change: ssh address ***
for cid in 110426 110401 111001 110412 110417 110408
do
scp ./all.txt mrashid2@c220g5-$cid.wisc.cloudlab.us:/root/keys
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us << EOF
sudo su -
cat /root/keys/all.txt >> /root/.ssh/authorized_keys
rm -rf /root/keys

cat >>/root/.ssh/config <<\__EOF
Host *
  StrictHostKeyChecking no
__EOF
chmod 0600 /root/.ssh/config
exit
exit
EOF
done
rm -rf all.txt

# *** Change: ssh address ***
for cid in 110426 110401 111001 110412 110417 110408
do
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us  << EOF
sudo su -

touch fb_test.txt tun_test.txt
yum -y install tmux tree

rm -rf filebench*
mkdir -p ~/localssd
cd ~/localssd
chown -R mrashid2 ./
git clone https://github.com/filebench/filebench.git
cd filebench/
libtoolize
aclocal
autoheader
automake --add-missing
autoconf
./configure
make
sudo make install
mkdir rpc_tuning_tests
cd ~

mkdir -p ~/localssd/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/localssd/miniconda3/miniconda.sh
bash ~/localssd/miniconda3/miniconda.sh -b -u -p ~/localssd/miniconda3
rm -rf ~/localssd/miniconda3/miniconda.sh
source ~/localssd/miniconda3/bin/activate
~/localssd/miniconda3/bin/conda init
exit

sudo su -
conda create --name ml_test_env --yes python=3.10 numpy pandas pytorch scikit-learn scipy tqdm fastparquet pyarrow py-xgboost matplotlib
conda activate ml_test_env
exit

exit
EOF
done

# Only for multiple client verification
# *** Change: ssh address ***
for cid in 110426 110401 111001 110412 110417
do
ssh -tt -p 22 mrashid2@c220g5-$cid.wisc.cloudlab.us << EOF
sudo su -
echo "node0 slots=20
node1 slots=20
node2 slots=20
node3 slots=20
node4 slots=20" > /root/hfile
mpirun --allow-run-as-root --hostfile /root/hfile --map-by node -np `cat /root/hfile|wc -l` hostname
exit
exit
EOF
done