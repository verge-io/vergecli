# Verge CLI Cookbook

Practical recipes for common verge-cli tasks. Each recipe includes a goal, steps, verification, and optional cleanup.

---

## Recipe 1: Getting Started

**Goal:** Install verge-cli and connect to your VergeOS instance.

### Steps

1. Install the CLI:

```bash
# Using uv (recommended)
uv tool install verge-cli

# Or using pip
pip install verge-cli
```

2. Run interactive setup to create a configuration profile:

```bash
vrg configure setup
```

This prompts for your VergeOS host URL, authentication method (token, API key, or username/password), and default output format. Config is saved to `~/.vrg/config.toml`.

3. Alternatively, use environment variables instead of a config file:

```bash
export VERGE_HOST=https://verge.example.com
export VERGE_TOKEN=your-api-token
```

### Verify

```bash
vrg system info
```

You should see your VergeOS cluster name, version, and node count.

### Check Your Config

```bash
vrg configure show
```

Displays the active profile and its settings (credentials are masked).

---

## Recipe 2: Managing Virtual Machines

**Goal:** Create, configure, and manage the lifecycle of a virtual machine.

### Steps

1. Create a VM with 2 GB RAM and 2 vCPUs:

```bash
vrg vm create --name web-server --ram 2048 --cpu 2
```

2. Inspect the VM to confirm its configuration:

```bash
vrg vm get web-server
```

3. Power on the VM and wait for it to reach running state:

```bash
vrg vm start web-server --wait
```

4. List all running VMs to confirm it is up:

```bash
vrg vm list --status running
```

5. Scale up memory while the VM is running (if supported) or after stopping it:

```bash
vrg vm update web-server --ram 4096
```

6. Gracefully stop the VM:

```bash
vrg vm stop web-server --wait
```

### Cleanup

Delete the VM when it is no longer needed. The `--force` flag powers it off first, and `--yes` skips the confirmation prompt:

```bash
vrg vm delete web-server --force --yes
```

---

## Recipe 3: Setting Up a Network

**Goal:** Create an internal network with DHCP, firewall rules, and a static host entry.

### Steps

1. Create a network with a CIDR range, gateway IP, and DHCP enabled:

```bash
vrg network create --name dev-net --cidr 10.0.0.0/24 --ip 10.0.0.1 --dhcp
```

2. Start the network:

```bash
vrg network start dev-net
```

3. Add a firewall rule to allow inbound SSH:

```bash
vrg network rule create dev-net \
  --action allow --direction inbound \
  --protocol tcp --port 22
```

4. Apply the firewall rules so they take effect:

```bash
vrg network apply-rules dev-net
```

5. Add a DHCP host override to assign a static lease:

```bash
vrg network host create dev-net \
  --hostname db-server --ip 10.0.0.50
```

### Verify

Ping the static host from the network's router to confirm connectivity:

```bash
vrg network diag ping dev-net --target 10.0.0.50
```

---

## Recipe 4: Configuring DNS

**Goal:** Set up DNS resolution with zones and records on an internal network.

### Steps

1. Create a DNS view to group your zones:

```bash
vrg network dns view create dev-net --name internal
```

2. Create a master zone under that view (use the view key returned in step 1):

```bash
vrg network dns zone create dev-net \
  --domain example.local --type master --view 1
```

3. Add an A record pointing `www` to a server IP (use the zone key returned in step 2):

```bash
vrg network dns record create dev-net 1 \
  --host www --type A --value 10.0.0.10 --ttl 3600
```

4. Add a CNAME record pointing `mail` to the `www` host:

```bash
vrg network dns record create dev-net 1 \
  --host mail --type CNAME --value www.example.local --ttl 3600
```

5. Apply DNS configuration so the changes take effect:

```bash
vrg network apply-dns dev-net
```

### Verify

Query the DNS server from the network to confirm resolution:

```bash
vrg network diag dns dev-net --host www.example.local
```

You should see `www.example.local` resolve to `10.0.0.10`.
