
# BeeGFS Server Setup


This page provides reference information for setting up BeeGFS parallel
filesystem servers for use with Omnia-managed clusters. Omnia deploys the
BeeGFS **client** on cluster nodes; the BeeGFS server infrastructure must be
configured independently before running `omnia.yml`.

## BeeGFS architecture overview


| Component | Description |
| --- | --- |
| **Management service** (`beegfs-mgmtd`) | Central registry that tracks all BeeGFS metadata and storage servers. Exactly one per filesystem. Lightweight; can run on existing infrastructure. |
| **Metadata service** (`beegfs-meta`) | Manages the filesystem namespace (directory structure, file attributes, stripe information). Deploy on low-latency storage (NVMe SSD recommended). |
| **Storage service** (`beegfs-storage`) | Stores actual file data in chunks. Deploy on nodes with high storage capacity and throughput (HDD arrays or NVMe). |
| **Client** (`beegfs-client`) | Kernel module mounted on compute nodes. Installed by Omnia via `software_config.json`. |

## Hardware recommendations


| Role | Minimum Hardware | Notes |
| --- | --- | --- |
| Management | 2 cores, 4 GB RAM, 10 GB disk | Very low resource requirements. Can be co-located with a metadata server. |
| Metadata | 8 cores, 32 GB RAM, NVMe SSD(s) | Metadata I/O is latency-sensitive. Use NVMe or fast SAS SSDs. RAID-1 for redundancy. |
| Storage | 8 cores, 32 GB RAM, HDD/SSD arrays | Throughput-optimized. Use JBOD or RAID-6 for large capacity. Size depends on total storage needs. |
| Network | 25 GbE or faster | Use dedicated NICs for BeeGFS traffic. 100 GbE recommended for high-throughput workloads. |

## Server installation


### Step 1: Add BeeGFS repository


```bash title="Run on: BeeGFS server"
# Import the BeeGFS GPG key
rpm --import https://www.beegfs.io/release/beegfs_7.4.3/gpg/GPG-KEY-beegfs

# Add the repository
cat > /etc/yum.repos.d/beegfs.repo << 'EOF'
[beegfs]
name=BeeGFS
baseurl=https://www.beegfs.io/release/beegfs_7.4.3/dists/rhel10
gpgcheck=1
gpgkey=https://www.beegfs.io/release/beegfs_7.4.3/gpg/GPG-KEY-beegfs
enabled=1
EOF
```



### Step 2: Install management service


On the management node:

```bash title="Run on: Management node"
dnf install -y beegfs-mgmtd
mkdir -p /data/beegfs/mgmtd
/opt/beegfs/sbin/beegfs-setup-mgmtd -p /data/beegfs/mgmtd
systemctl enable --now beegfs-mgmtd
```



### Step 3: Install metadata service


On each metadata server:

```bash title="Run on: Metadata server"
dnf install -y beegfs-meta
mkdir -p /data/beegfs/meta
/opt/beegfs/sbin/beegfs-setup-meta -p /data/beegfs/meta \
    -s <unique_server_id> -m <mgmtd_hostname>
systemctl enable --now beegfs-meta
```


!!! note

    `<unique_server_id>` is a positive integer unique across all metadata
    servers. `<mgmtd_hostname>` is the hostname or IP of the management
    service.

### Step 4: Install storage service


On each storage server:

```bash title="Run on: Storage server"
dnf install -y beegfs-storage
mkdir -p /data/beegfs/storage
/opt/beegfs/sbin/beegfs-setup-storage -p /data/beegfs/storage \
    -s <unique_server_id> -i <storage_target_id> -m <mgmtd_hostname>
systemctl enable --now beegfs-storage
```


!!! note

    For multiple storage targets on a single node, run `beegfs-setup-storage`
    once per target with different `-p` paths and `-i` target IDs.

### Step 5: Verify the server setup


```bash title="Run on: BeeGFS server"
# Check registered servers (run from any node with beegfs-ctl)
beegfs-ctl --listnodes --nodetype=meta
beegfs-ctl --listnodes --nodetype=storage

# Check filesystem health
beegfs-ctl --listtargets --state
```



## Network configuration


| Configuration | Description |
| --- | --- |
| `connInterfacesFile` | File listing network interfaces BeeGFS should use, one per line. Place on all servers and clients. Example contents: `enp175s0f0`. |
| `connNetFilterFile` | File listing allowed subnets, one per line (CIDR notation). Restricts BeeGFS traffic to specific networks. Example: `10.10.0.0/24`. |
| `connRDMAEnabled` | Set to `true` in the BeeGFS config files to enable RDMA (InfiniBand or RoCEv2) for data transfer. Requires compatible NICs. |

```bash title="Example: BeeGFS network configuration files"
# Example connInterfacesFile (/etc/beegfs/connInterfacesFile)
enp175s0f0

# Example connNetFilterFile (/etc/beegfs/connNetFilterFile)
10.10.0.0/24
```



## Tuning parameters


| Parameter | Default | Recommendation |
| --- | --- | --- |
| `tuneNumWorkers` (meta) | 8 | Set to number of CPU cores on the metadata server. |
| `tuneNumWorkers` (storage) | 12 | Set to number of CPU cores on the storage server. |
| `tuneFileWriteSize` | 512 KB | Increase to 1--4 MB for large sequential writes (AI training data). |
| `tuneFileReadSize` | 512 KB | Increase to 1--4 MB for large sequential reads. |
| `connMaxInternodeNum` | 32 | Increase for clusters with > 100 clients. |

## Omnia client integration


Once the BeeGFS server infrastructure is running, configure the Omnia-managed
clients:

1. Set `beegfs_enabled: true` in `storage_config.yml`.
2. Set `beegfs_mgmt_server` to the management service hostname or IP.
3. Optionally set `beegfs_mount_path`, `beegfs_connInterfacesFile`, and
   `beegfs_connNetFilterFile`.
4. Add `beegfs_client` to the appropriate functional groups in
   `software_config.json`.
5. Run `omnia.yml` to deploy clients.

!!! info

    - [Storage Config](../Configuration/storage_config.md) -- BeeGFS client
      configuration parameters.
    - [Storage](../SupportMatrix/storage.md) -- Supported storage platforms.
    - [BeeGFS Documentation](https://doc.beegfs.io/latest/) -- Official
      BeeGFS documentation.
