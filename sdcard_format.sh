#!/bin/bash -xe
dev=/dev/mmc0

if [[ ! -z "$1" ]]; then
	dev="$1"
fi


sfdisk "${dev}" << EOF
,512M,b,*
,,83,-
EOF

if [[ ! -e "${dev}1" ]]; then
    dev="${dev}p"
fi

mkfs.vfat "${dev}1"
mkfs.ext4 "${dev}2"

mnt="$(mktemp -d)"

mount "${dev}1" "${mnt}"
tar -Jxvf bootfs.tar.xz -C "${mnt}"
umount "${mnt}"

mount "${dev}2" "${mnt}"
tar -Jxvf rootfs.tar.xz -C "${mnt}"
umount "${mnt}"

rmdir "${mnt}"

sync
