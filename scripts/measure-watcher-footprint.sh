#!/usr/bin/env bash
# measure-watcher-footprint.sh — Phase 0 test gate measurement primitive
#
# Plan: .claude/plans/jiggly-honking-cascade.md (Change 3)
# Purpose: captures Context Engine watcher daemon phys_footprint, evaluates
# four triggers, and writes ~/.context-engine/PHASE2_TRIGGERED on any exceed.
# Invoked daily at 04:00 by com.ai-governance.context-engine-measure launchd
# plist (installed by context-engine-service install on macOS).
#
# Exit codes:
#   0 = pass (all triggers clear)
#   1 = measurement error (no PID, vmmap denied, missing baseline)
#   2 = trigger fired (marker file written, Phase 2 activation required)
#
# Thresholds (measurement-derived per plan Change 3 and Contrarian Finding 3):
#   Trigger 1: steady_mb > 1.5 × baseline_steady_mb
#              (2026-04-17 recalibration: post-Phase-2 this detects regression
#              against the equilibrium baseline, not compliance with a 40%
#              drop from a pre-fix reference. Fires on ≥50% growth from the
#              post-Phase-2 equilibrium captured in phase0-baseline.txt.)
#   Trigger 2: measured_slope_mb_per_h > 0.5 × baseline_slope_mb_per_h
#              (disabled if baseline_slope < 8 MB/h — noise floor)
#   Trigger 3: peak_mb > 7500 (7.3 GB — post-Phase-2 recalibration, 2026-04-17)
#              Was 3072 (3.0 GB) pre-Phase-2. Watcher now hosts torch+models
#              via the IPC embedding server, so single-process peak is
#              structurally higher. Cross-process total (Trigger 4) is the
#              architectural signal for Phase 2 sufficiency.
#   Trigger 4: cross-process total phys > 8192 (8.0 GB)
#
# The baseline file at ~/.context-engine/logs/phase0-baseline.txt MUST exist
# with the following key=value entries (populated by Verification step 1):
#   baseline_steady_mb=<int>
#   baseline_peak_mb=<int>
#   baseline_slope_mb_per_h=<float>  (or "0" to disable Trigger 2)

set -uo pipefail

CE_HOME="${HOME}/.context-engine"
LOGS_DIR="${CE_HOME}/logs"
HEARTBEAT="${CE_HOME}/watcher-heartbeat.json"
PID_FILE="${CE_HOME}/watcher.pid"
BASELINE_FILE="${LOGS_DIR}/phase0-baseline.txt"
MEASUREMENTS_LOG="${LOGS_DIR}/phase0-measurements.log"
TRIGGER_MARKER="${CE_HOME}/PHASE2_TRIGGERED"

mkdir -p "${LOGS_DIR}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

die_measurement_error() {
  local msg="$1"
  echo "ERROR: ${msg}" >&2
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "${ts} ERROR ${msg}" >> "${MEASUREMENTS_LOG}"
  exit 1
}

# Resolve watcher PID. Prefer heartbeat JSON (authoritative) > pid file > pgrep.
resolve_watcher_pid() {
  local pid=""
  if [ -f "${HEARTBEAT}" ]; then
    pid=$(python3 -c "import json,sys
try:
  print(json.load(open('${HEARTBEAT}'))['pid'])
except Exception:
  sys.exit(1)" 2>/dev/null || echo "")
  fi
  if [ -z "${pid}" ] && [ -f "${PID_FILE}" ]; then
    pid=$(cat "${PID_FILE}" 2>/dev/null || echo "")
  fi
  if [ -z "${pid}" ]; then
    pid=$(pgrep -f "context-engine-watcher" 2>/dev/null | head -1 || echo "")
  fi
  echo "${pid}"
}

# Capture phys_footprint for a single PID in MB (integer).
# macOS: vmmap -summary | grep "Physical footprint:"
# Linux: /proc/$PID/status VmRSS + VmSwap
capture_phys_footprint_mb() {
  local pid="$1"
  if [ -z "${pid}" ] || ! kill -0 "${pid}" 2>/dev/null; then
    echo "0"
    return
  fi
  case "$(uname -s)" in
    Darwin)
      vmmap -summary "${pid}" 2>/dev/null | awk '
        /^Physical footprint:/ {
          val = $3
          # Normalize to MB (int). Handles G/M/K suffixes.
          if (val ~ /G$/) { sub("G", "", val); printf "%d\n", val * 1024; exit }
          if (val ~ /M$/) { sub("M", "", val); printf "%d\n", val; exit }
          if (val ~ /K$/) { sub("K", "", val); printf "%d\n", val / 1024; exit }
          printf "%d\n", val / 1048576; exit
        }
      '
      ;;
    Linux)
      if [ ! -r "/proc/${pid}/status" ]; then
        echo "0"
        return
      fi
      awk '
        /^VmRSS:/  { rss  = $2 }
        /^VmSwap:/ { swap = $2 }
        END { printf "%d\n", (rss + swap) / 1024 }
      ' "/proc/${pid}/status"
      ;;
    *)
      echo "0"
      ;;
  esac
}

# Capture peak phys_footprint (macOS only; Linux falls back to VmPeak + VmSwap).
capture_peak_mb() {
  local pid="$1"
  if [ -z "${pid}" ] || ! kill -0 "${pid}" 2>/dev/null; then
    echo "0"
    return
  fi
  case "$(uname -s)" in
    Darwin)
      vmmap -summary "${pid}" 2>/dev/null | awk '
        /^Physical footprint \(peak\):/ {
          val = $4
          if (val ~ /G$/) { sub("G", "", val); printf "%d\n", val * 1024; exit }
          if (val ~ /M$/) { sub("M", "", val); printf "%d\n", val; exit }
          if (val ~ /K$/) { sub("K", "", val); printf "%d\n", val / 1024; exit }
          printf "%d\n", val / 1048576; exit
        }
      '
      ;;
    Linux)
      awk '
        /^VmPeak:/ { peak = $2 }
        /^VmSwap:/ { swap = $2 }
        END { printf "%d\n", (peak + swap) / 1024 }
      ' "/proc/${pid}/status" 2>/dev/null || echo "0"
      ;;
    *)
      echo "0"
      ;;
  esac
}

# Sum phys_footprint across ALL Python processes matching our pattern set.
# Cross-process trigger (Trigger 4) — detects cause #2 (model duplication).
capture_cross_process_total_mb() {
  local total=0
  local pids
  case "$(uname -s)" in
    Darwin)
      pids=$(pgrep -f "context-engine-watcher|ai_governance_mcp|ai-context-engine" 2>/dev/null || true)
      ;;
    Linux)
      pids=$(pgrep -f "context-engine-watcher|ai_governance_mcp|ai-context-engine" 2>/dev/null || true)
      ;;
    *)
      echo "0"
      return
      ;;
  esac
  for p in ${pids}; do
    mb=$(capture_phys_footprint_mb "${p}")
    total=$((total + mb))
  done
  echo "${total}"
}

# Compute process uptime in hours (float). Falls back to "0" on error.
compute_uptime_hours() {
  local pid="$1"
  case "$(uname -s)" in
    Darwin)
      # ps -o etime returns [DD-]HH:MM:SS or MM:SS
      etime=$(ps -o etime= -p "${pid}" 2>/dev/null | tr -d ' ')
      python3 -c "
import sys
et = '${etime}'
try:
    if '-' in et:
        days, rest = et.split('-', 1)
        days = int(days)
    else:
        days, rest = 0, et
    parts = rest.split(':')
    if len(parts) == 3:
        h, m, s = map(int, parts)
    elif len(parts) == 2:
        h, m, s = 0, int(parts[0]), int(parts[1])
    else:
        h = m = s = 0
    total_h = days * 24 + h + m / 60 + s / 3600
    print(f'{total_h:.2f}')
except Exception:
    print('0')
" 2>/dev/null || echo "0"
      ;;
    Linux)
      starttime=$(stat -c %Y "/proc/${pid}" 2>/dev/null || echo "0")
      now=$(date +%s)
      python3 -c "print(f'{(${now} - ${starttime}) / 3600:.2f}')" 2>/dev/null || echo "0"
      ;;
    *)
      echo "0"
      ;;
  esac
}

# Read a key=value from the baseline file.
read_baseline_value() {
  local key="$1"
  if [ ! -f "${BASELINE_FILE}" ]; then
    echo ""
    return
  fi
  grep "^${key}=" "${BASELINE_FILE}" | tail -1 | cut -d= -f2- | tr -d ' '
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# 1. Resolve PID
PID=$(resolve_watcher_pid)
if [ -z "${PID}" ]; then
  die_measurement_error "no watcher PID found (heartbeat missing, pid file missing, no matching process)"
fi

# 2. Capture measurements
STEADY_MB=$(capture_phys_footprint_mb "${PID}")
PEAK_MB=$(capture_peak_mb "${PID}")
UPTIME_H=$(compute_uptime_hours "${PID}")
TOTAL_MB=$(capture_cross_process_total_mb)

if [ "${STEADY_MB}" = "0" ]; then
  die_measurement_error "phys_footprint capture failed for PID ${PID}"
fi

# 3. Read baseline (required for triggers 1 and 2)
BASELINE_STEADY=$(read_baseline_value "baseline_steady_mb")
BASELINE_SLOPE=$(read_baseline_value "baseline_slope_mb_per_h")
if [ -z "${BASELINE_STEADY}" ]; then
  die_measurement_error "baseline_steady_mb missing from ${BASELINE_FILE} (run Verification step 1 first)"
fi

# 4. Compute current slope (approximate: delta vs. last measurement in log).
# On first run this will be 0; accurate slope requires ≥2 samples in the log.
LAST_LINE=$(tail -n 1 "${MEASUREMENTS_LOG}" 2>/dev/null | grep -v ERROR || true)
MEASURED_SLOPE="0"
if [ -n "${LAST_LINE}" ]; then
  LAST_STEADY=$(echo "${LAST_LINE}" | awk '{print $2}' | grep -oE '[0-9]+' | head -1 || echo "0")
  LAST_UPTIME=$(echo "${LAST_LINE}" | awk '{print $4}' | grep -oE '[0-9.]+' | head -1 || echo "0")
  if [ "${LAST_STEADY}" != "0" ] && [ "${LAST_UPTIME}" != "0" ]; then
    MEASURED_SLOPE=$(python3 -c "
try:
    delta_mb = ${STEADY_MB} - ${LAST_STEADY}
    delta_h = ${UPTIME_H} - ${LAST_UPTIME}
    if delta_h > 0:
        print(f'{delta_mb / delta_h:.1f}')
    else:
        print('0')
except Exception:
    print('0')
" 2>/dev/null || echo "0")
  fi
fi

# 5. Evaluate triggers (all four are independent)
TRIGGERS_FIRED=""

# Trigger 1: regression detection — steady grew ≥50% from post-Phase-2 baseline
T1_THRESHOLD=$(python3 -c "print(int(${BASELINE_STEADY} * 1.5))")
if [ "${STEADY_MB}" -gt "${T1_THRESHOLD}" ]; then
  TRIGGERS_FIRED="${TRIGGERS_FIRED}T1(steady=${STEADY_MB}>${T1_THRESHOLD}) "
fi

# Trigger 2: measured slope ≤ 0.5 × baseline slope (disabled if baseline < 8 MB/h)
if [ -n "${BASELINE_SLOPE}" ]; then
  T2_DISABLED=$(python3 -c "print(1 if float('${BASELINE_SLOPE}' or 0) < 8 else 0)" 2>/dev/null || echo 1)
  if [ "${T2_DISABLED}" = "0" ]; then
    T2_THRESHOLD=$(python3 -c "print(f'{float(\"${BASELINE_SLOPE}\") * 0.5:.1f}')")
    T2_EXCEED=$(python3 -c "print(1 if float('${MEASURED_SLOPE}') > float('${T2_THRESHOLD}') else 0)" 2>/dev/null || echo 0)
    if [ "${T2_EXCEED}" = "1" ]; then
      TRIGGERS_FIRED="${TRIGGERS_FIRED}T2(slope=${MEASURED_SLOPE}>${T2_THRESHOLD}) "
    fi
  fi
fi

# Trigger 3: session peak < 7.3 GB (7500 MB, post-Phase-2 recalibration 2026-04-17)
if [ "${PEAK_MB}" -gt 7500 ]; then
  TRIGGERS_FIRED="${TRIGGERS_FIRED}T3(peak=${PEAK_MB}>7500) "
fi

# Trigger 4: cross-process total < 8 GB (8192 MB)
if [ "${TOTAL_MB}" -gt 8192 ]; then
  TRIGGERS_FIRED="${TRIGGERS_FIRED}T4(total=${TOTAL_MB}>8192) "
fi

# 6. Write measurement log entry
printf '%s steady=%sMB peak=%sMB uptime=%sh slope=%sMB/h total=%sMB triggers=%s\n' \
  "${TS}" "${STEADY_MB}" "${PEAK_MB}" "${UPTIME_H}" "${MEASURED_SLOPE}" "${TOTAL_MB}" "${TRIGGERS_FIRED:-none}" \
  >> "${MEASUREMENTS_LOG}"

# 7. Output summary to stdout
echo "Phase 0 measurement @ ${TS}"
echo "  steady=${STEADY_MB}MB peak=${PEAK_MB}MB uptime=${UPTIME_H}h slope=${MEASURED_SLOPE}MB/h"
echo "  cross_process_total=${TOTAL_MB}MB"
echo "  baseline_steady=${BASELINE_STEADY}MB baseline_slope=${BASELINE_SLOPE:-n/a}MB/h"

if [ -z "${TRIGGERS_FIRED}" ]; then
  echo "  triggers: none fired (pass)"
  exit 0
fi

# 8. Trigger fired — write marker and exit 2
{
  echo "${TS} PHASE 2 TRIGGER FIRED"
  echo "triggers=${TRIGGERS_FIRED}"
  echo "steady_mb=${STEADY_MB}"
  echo "peak_mb=${PEAK_MB}"
  echo "uptime_h=${UPTIME_H}"
  echo "measured_slope_mb_per_h=${MEASURED_SLOPE}"
  echo "cross_process_total_mb=${TOTAL_MB}"
  echo "baseline_steady_mb=${BASELINE_STEADY}"
  echo "baseline_slope_mb_per_h=${BASELINE_SLOPE:-n/a}"
  echo ""
  echo "ACTION: re-enter BACKLOG.md #49, schedule contrarian-reviewed design spike"
  echo "        for shared embedding service OR direct optimum+tokenizers rewrite."
  echo "        Clear this file after escalation: rm ${TRIGGER_MARKER}"
} > "${TRIGGER_MARKER}"

echo "  triggers FIRED: ${TRIGGERS_FIRED}"
echo "  marker written: ${TRIGGER_MARKER}"
exit 2
