# VMware Lab Notes

This document describes how to run the Telecom Integration Infrastructure Lab
inside a VMware virtual machine — the recommended environment for reproducing
a realistic telecom integration workflow on a developer workstation.

---

## Recommended VMware Setup

| Setting         | Value                        |
|-----------------|------------------------------|
| Hypervisor      | VMware Workstation 17 / VMware Player / Fusion |
| Guest OS        | Ubuntu Server 22.04 LTS (64-bit) |
| vCPUs           | 2                            |
| RAM             | 2 GB                         |
| Disk            | 20 GB thin-provisioned       |
| Network adapter | Host-only (vmnet1) — isolates lab traffic from the host LAN |

---

## Initial VM Configuration

### 1. Install build dependencies inside the VM

```bash
sudo apt update
sudo apt install -y cmake g++ python3 python3-pip python3-venv git openssh-server
```

### 2. Install open-vm-tools (VMware guest utilities)

```bash
sudo apt install -y open-vm-tools
sudo systemctl enable --now open-vm-tools
```

Verify VMware Tools are running:

```bash
vmware-toolsd --version
# Expected: VMware Tools daemon, version 12.x.x
```

### 3. Check network connectivity from host to VM

```bash
# On the host, find the VM IP assigned by vmnet1:
ip addr show vmnet1

# From the host, ping the VM:
ping 192.168.x.y

# SSH into the VM from the host:
ssh <vm-user>@192.168.x.y
```

---

## Running the SSH Node Check Against the VM

Once the VM is reachable via SSH, use `ssh_node_check.py` to simulate
a telecom node health check:

```bash
# From the host (or another VM acting as the NOC):
python scripts/ssh_node_check.py \
    --host 192.168.x.y \
    --user <vm-user> \
    --key ~/.ssh/id_rsa
```

Expected output:

```
[SSH] Connecting to <vm-user>@192.168.x.y …

============================================================
  Telecom Node SSH Check — 192.168.x.y
============================================================

[HOSTNAME    ] [OK]
    aveiro-lab-node

[UPTIME      ] [OK]
    up 1 hour, 3 minutes, load average: 0.05, 0.04, 0.01

[DISK        ] [OK]
    /dev/sda1  19G  3.2G  15G  18% /

[NETWORK     ] [OK]
    2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> ...

SUMMARY: All 4 check(s) passed.
```

---

## Simulating a Telecom Node Inside the VM

Edit `config/telecom_nodes.csv` to include the VM's IP address:

```csv
node_id,technology,ip_address,ssh_port,service_name,expected_latency_ms
VM-LAB-001,5G,192.168.x.y,22,small-cell-agent,18
```

Then run the C++ integration checker from the host or VM:

```bash
./build/telecom_integration_checker config/telecom_nodes.csv
```

---

## Snapshot Strategy

Use VMware snapshots to preserve known-good states:

```
Snapshot 1 — "Fresh install"         (before any project setup)
Snapshot 2 — "Build environment ready"  (after apt installs)
Snapshot 3 — "Tests passing"         (after first successful CI run)
```

To take a snapshot via vmrun (VMware CLI):

```bash
vmrun snapshot /path/to/vm.vmx "Build environment ready"
vmrun listSnapshots /path/to/vm.vmx
vmrun revertToSnapshot /path/to/vm.vmx "Build environment ready"
```

---

## Firewall Validation in the VM Environment

To simulate firewall rule validation between two VMs on vmnet1:

1. Create a second VM (acts as the NOC / monitoring host).
2. Add both VMs to `config/telecom_nodes.csv`.
3. Configure `iptables` on the target VM to restrict SSH to the NOC IP:

```bash
sudo iptables -A INPUT -p tcp --dport 22 -s <noc-vm-ip> -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j DROP
```

4. Run `firewall_rule_validator.py` to validate the intended policy matches
   the configured rules:

```bash
python scripts/firewall_rule_validator.py --rules config/firewall_rules.json
```

---

## Useful VMware / Linux Commands for Telecom Lab Work

```bash
# Check VM IP assigned by DHCP on vmnet1
ip addr show ens33

# List network interfaces and their state
ip link show

# Test SSH port reachability (from host or another VM)
nc -zv 192.168.x.y 22

# Monitor network traffic on the SSH port (requires tcpdump)
sudo tcpdump -i ens33 port 22

# Check open-vm-tools status
systemctl status open-vm-tools

# Shared folder (if VMware shared folders are enabled)
vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other
```
