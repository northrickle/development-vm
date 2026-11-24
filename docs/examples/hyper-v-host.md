# Using Hyper-V to host the development VM

This optional example creates an Ubuntu VM on Windows 11 Pro or Enterprise.
Enable Hyper-V, create the VM, then verify connectivity. Host configuration is
outside the Ubuntu playbook's scope; other host setups can also be used.

## Overview

- **Run on:** Windows 11 Pro or Enterprise, manually.
- **Goal:** create an Ubuntu VM with ordinary NAT networking.
- **Steps:** enable Hyper-V → create the VM → verify SSH and internet access.
- **Automation:** Ansible configures only Ubuntu accounts and development tools.

## 1. Enable Hyper-V

1. Enable **Hyper-V** in Windows Features.
2. Restart Windows.
3. Open **Hyper-V Manager**.

## 2. Create the VM

1. Create a **Generation 2** VM using the Ubuntu Server 26.04 LTS ISO.
2. Start with **8 vCPUs, 16 GB RAM and 200 GB disk**; adjust to host capacity.
3. Select **Microsoft UEFI Certificate Authority** for Linux Secure Boot.
4. Attach its network adapter to **Default Switch** for NAT/DHCP.
5. Continue with [Ubuntu installation](../../README.md#2-install-ubuntu).

Keep Windows' existing firewall configuration. This project adds no custom
Hyper-V ACLs, IPv6 blocks, guest firewall rules or port forwarding.

## 3. Verify access

- [ ] Ubuntu receives a network configuration and can resolve names.
- [ ] Ubuntu can access the internet.
- [ ] Windows can connect with `ssh vm` after SSH setup.
- [ ] Windows can open an application listening on the VM interface.
- [ ] Connectivity still works after restarting the VM.

Default Switch addressing may change. Update the local SSH alias if the VM's
address changes.

**Network limitation:** NAT is not isolation from the host or LAN. Programs in
the VM may contact reachable services. Protection of the host and other devices
from untrusted code is a separate workstation/network security concern.

References: [Enable Hyper-V](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/install-hyper-v?pivots=windows),
[Linux Secure Boot](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/plan/should-i-create-a-generation-1-or-2-virtual-machine-in-hyper-v).
