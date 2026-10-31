# VoltageOS 16 (Android 16) Local Build Guide for Redmi Note 10 5G (`camellia`)
**Target Device:** Xiaomi Redmi Note 10 5G / Poco M3 Pro 5G (`camellia` / `camellian`)  
**Target OS:** VoltageOS 16 with Native Savitech LHDC V3/V5  
**Hardware Detected:** Intel Core 7 240H (10 Cores / 16 Threads), 16 GB RAM, 468 GB Free SSD Space  

---

## Prerequisites (One-time Setup)

### Step 1: Install WSL2 (Ubuntu)
Because WSL is not yet installed on this PC, install it by opening **PowerShell as Administrator**:
```powershell
wsl --install -d Ubuntu-24.04
```
* Windows will download and enable the Virtual Machine Platform.
* If Windows prompts you to **restart your PC**, reboot.

### Step 2: Open Ubuntu & Set Username
1. After rebooting, open **Ubuntu 24.04** from your Windows Start Menu.
2. It will ask you to enter a **UNIX username** and **password** (choose anything you like, e.g. `sksal`).

---

## Starting the Build

Once inside your Ubuntu terminal, run this single command:

```bash
bash /mnt/e/DATA/Projects/LHDC/voltage_build/build_voltage.sh
```

### What This Script Does Automatically:
1. **Configures the Build Environment:** Installs Java 21, Clang, build tools, and sets up `ccache` (accelerates re-compilation).
2. **Initializes VoltageOS 16:** Syncs the Android 16 platform source tree.
3. **Pulls `camellia` Device Trees:** Injects device tree, proprietary vendor files, and kernel into `.repo/local_manifests/`.
4. **Applies Savitech LHDC Native Patches:** Patches `packages/modules/Bluetooth` and `packages/apps/Settings` with our verified Savitech LHDC stack.
5. **Compiles the ROM:** Executes `mka bacon` utilizing all 16 CPU threads.
6. **Exports Flashable Zip:** Copies the compiled `VoltageOS-16.0-camellia-UNOFFICIAL.zip` directly to:
   `e:\DATA\Projects\LHDC\voltage_build\out\`

---

## Memory & Performance Optimization
We have already generated and installed [`C:\Users\SKSAL\.wslconfig`](file:///C:/Users/SKSAL/.wslconfig) on your system with the following optimal settings:
* **WSL RAM:** 12 GB (leaves 4 GB for Windows host)
* **WSL Swap:** 16 GB (prevents out-of-memory errors during C++ linking)
* **CPU Threads:** 16
