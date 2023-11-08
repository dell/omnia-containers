
``raid1_rh.sh``

    This partitioning script is intended to be used on RHEL Operating systems to configure RAID1 across 2 physical disks.
    Composed of 2 parts:

    * the logic to select the disks to setup RAID
    * the logic to generate the partition scheme and save it to /tmp/partitionfile in the installer.

