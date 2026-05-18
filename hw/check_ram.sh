#!/bin/bash

echo "========================================"
echo "  ADVANCED CPU + MEMORY LATENCY AUDIT"
echo "  (Intel DDR5 / HFT-style diagnostics)"
echo "========================================"
echo ""

########################################
# 1. CPU TOPOLOGY
########################################
echo "1) CPU Topology (cores, threads, NUMA)"
echo "Command: lscpu"
echo "What it does: Shows CPU layout, NUMA nodes, caches"
echo "Why it matters: Determines scheduling + cache locality"
echo ""
lscpu | egrep "Model name|CPU\\(s\\)|Thread|Core|Socket|NUMA|MHz"
echo ""
echo "----------------------------------------"
echo ""

########################################
# 2. REAL-TIME CPU FREQUENCY
########################################
echo "2) CPU Frequency Snapshot"
echo "Command: /proc/cpuinfo"
echo "What it does: Shows current per-core frequency"
echo "Why it matters: Detects turbo stability and jitter"
echo ""
grep "cpu MHz" /proc/cpuinfo | head -10
echo ""
echo "----------------------------------------"
echo ""

########################################
# 3. MEMORY SPEED (PRIMARY CHECK)
########################################
echo "3) Memory Speed (Primary Source)"
echo "Command: dmidecode -t memory"
echo "What it does: Reads SPD + BIOS-configured memory speed"
echo "Why it matters: Confirms actual MT/s vs BIOS expectation"
echo ""
sudo dmidecode -t memory | egrep -i "Size|Speed|Configured Memory Speed|Type|Rank"
echo ""
echo "NOTE: 'Configured Memory Speed' = REAL running MT/s target"
echo ""
echo "----------------------------------------"
echo ""

########################################
# 4. MEMORY ARCHITECTURE (DIMM + RANK LOAD)
########################################
echo "4) Memory Physical Layout (DIMM + Rank load)"
echo "Command: lshw -class memory"
echo "What it does: Shows DIMM placement, width, clock hints"
echo "Why it matters: Rank + channel load affects IMC stress + latency"
echo ""
sudo lshw -class memory | egrep -i "bank|size|clock|width|description"
echo ""
echo "----------------------------------------"
echo ""

########################################
# 5. SPD DEEP INSPECTION (BEST SOURCE OF TRUTH)
########################################
echo "5) SPD / DIMM Capability Breakdown"
echo "Command: decode-dimms"
echo "What it does: Reads JEDEC SPD tables"
echo "Why it matters: Shows rank config + supported MT/s bins"
echo ""
if command -v decode-dimms >/dev/null 2>&1; then
    sudo decode-dimms | egrep -i "rank|speed|type|voltage|timing" | head -50
else
    echo "decode-dimms not installed (optional tool from i2c-tools)"
fi
echo ""
echo "----------------------------------------"
echo ""

########################################
# 6. MEMORY CONTROLLER BEHAVIOUR (Gearing proxy)
########################################
echo "6) Memory Controller / Gear Mode Indicators (Intel DDR5 proxy)"
echo "Command: dmesg | grep -i gear"
echo "What it does: Looks for memory controller training mode hints"
echo "Why it matters: Gear mode impacts latency (similar to UCLK 1:2 effect)"
echo ""
sudo dmesg | grep -i gear | tail -20
echo ""
echo "If empty: kernel did not expose gear state (normal on some setups)"
echo ""
echo "----------------------------------------"
echo ""

########################################
# 7. NUMA TOPOLOGY
########################################
echo "7) NUMA Topology"
echo "Command: numactl --hardware"
echo "What it does: Shows memory nodes and CPU binding domains"
echo "Why it matters: NUMA imbalance increases latency variance"
echo ""
numactl --hardware
echo ""
echo "----------------------------------------"
echo ""

########################################
# 8. CACHE HIERARCHY
########################################
echo "8) Cache Hierarchy"
echo "Command: lscpu | grep cache"
echo "What it does: Shows L1/L2/L3 cache sizes"
echo "Why it matters: Cache hit rate dominates latency performance"
echo ""
lscpu | grep -i cache
echo ""
echo "----------------------------------------"
echo ""

########################################
# 9. MEMORY PRESSURE
########################################
echo "9) Memory Pressure Snapshot"
echo "Command: /proc/meminfo"
echo "What it does: Shows memory usage, pressure signals"
echo "Why it matters: High pressure increases tail latency"
echo ""
head -n 20 /proc/meminfo
echo ""
echo "----------------------------------------"
echo ""

########################################
# 10. INTERRUPT DISTRIBUTION (JITTER SOURCE)
########################################
echo "10) IRQ Distribution"
echo "Command: /proc/interrupts"
echo "What it does: Shows interrupt load per core"
echo "Why it matters: Poor IRQ balance = latency spikes"
echo ""
head -n 20 /proc/interrupts
echo ""
echo "----------------------------------------"
echo ""

########################################
# 11. CPU GOVERNOR / POWER STATE
########################################
echo "11) CPU Power / Governor State"
echo "Command: cpupower frequency-info"
echo "What it does: Shows scaling + boost policy"
echo "Why it matters: Prevents hidden power-saving latency modes"
echo ""
if command -v cpupower >/dev/null 2>&1; then
    cpupower frequency-info | head -30
else
    echo "cpupower not installed (install linux-tools-common)"
fi
echo ""
echo "----------------------------------------"
echo ""

########################################
# 12. QUICK INTERPRETATION SUMMARY
########################################
echo "12) INTERPRETATION GUIDE"
echo ""
echo "GOOD SIGNS:"
echo "- Configured Memory Speed matches BIOS target (e.g. 5600/6400/7000)"
echo "- Rank = 1R or balanced 2R across channels"
echo "- No swap usage"
echo "- IRQs spread across cores"
echo "- CPU frequency stable under load"
echo ""
echo "BAD SIGNS:"
echo "- Memory speed lower than expected (fallback training)"
echo "- Heavy dual-rank + 4 DIMM load"
echo "- Gear mode changes under load (if visible)"
echo "- NUMA imbalance"
echo "- Frequent CPU frequency oscillation"
echo ""
echo "========================================"
echo "  END OF ADVANCED AUDIT"
echo "========================================"
