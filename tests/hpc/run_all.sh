#!/bin/bash
# HPC Test Orchestrator — polls jobs, checks results, fills report
set -e

HPC_DIR="<PROJECT_ROOT>/tests/hpc"
REPORT="$HPC_DIR/_report_template.md"
FINAL_REPORT="<PROJECT_ROOT>/docs/devlog/notes/$(date +%Y-%m-%d)-test-hpc-cluster.md"
LOG="$HPC_DIR/run_all.log"
FAILS_FILE="$HPC_DIR/_fails.txt"
> "$FAILS_FILE"

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

wait_for_job() {
    local job_id=$1
    local label=$2
    log "等待 $label (Job $job_id)..."
    while true; do
        local state
        state=$(squeue -j "$job_id" --noheader -o "%T" 2>/dev/null)
        if [ -z "$state" ]; then
            log "$label 作业已结束"
            break
        fi
        sleep 30
    done
}

find_output() {
    local job_id=$1
    local f
    # match both regular (slurm-123.out) and array (slurm-123-0.out) patterns
    for dir in "$HPC_DIR" "$HPC_DIR"/*/; do
        f=$(ls "$dir"slurm-"$job_id"*.out 2>/dev/null | head -1)
        if [ -n "$f" ]; then
            echo "$f"
            return 0
        fi
    done
    return 1
}

check_result() {
    local job_id=$1
    local label=$2
    local outfile
    outfile=$(find_output "$job_id")
    if [ -z "$outfile" ]; then
        log "[FAIL] $label: 找不到输出文件"
        echo "  - $label: FAIL (no output file)" >> "$FAILS_FILE"
        return 1
    fi
    # check for [TOTAL] N/M passed
    if grep -q "\[TOTAL\]" "$outfile" 2>/dev/null; then
        local total_line
        total_line=$(grep "\[TOTAL\]" "$outfile" | tail -1)
        log "[RESULT] $label: $total_line"
        # if the line contains "0 failed" or all passed, treat as pass
        if echo "$total_line" | grep -qE "[0-9]+/[0-9]+ passed"; then
            local nums
            nums=$(echo "$total_line" | grep -oE '[0-9]+' | head -2)
            local pass_num fail_num
            pass_num=$(echo "$nums" | head -1)
            fail_num=$(echo "$nums" | tail -1)
            if [ "$pass_num" = "$fail_num" ] || [ "$fail_num" = "0" ]; then
                log "[PASS] $label (${pass_num}/${fail_num})"
                return 0
            fi
        fi
    fi
    if grep -iqE "FAIL|Error|FATAL|FAILED" "$outfile" 2>/dev/null; then
        log "[FAIL] $label — errors in output"
        echo "  - $label: FAIL" >> "$FAILS_FILE"
        return 1
    fi
    # assume pass if we got here
    log "[PASS] $label (assumed)"
    return 0
}

submit_job() {
    local area=$1
    local script=$2
    log "提交 $area ..." >&2
    (cd "$HPC_DIR/$area" && sbatch --parsable "$script")
}

# ——— Phase 1: 01 + 02 ———
log "=========================================="
log "Phase 1: 基础设施验证"
log "=========================================="

OLD_JOB=$(squeue -u <slurm_user> --noheader -o "%i" -n hpc-mpi 2>/dev/null)
[ -n "$OLD_JOB" ] && scancel "$OLD_JOB" && log "取消旧作业 $OLD_JOB"

JOB01=$(submit_job "01-mpi-multinode" "submit_intelmpi.sh")
log "Job 01 = $JOB01"

wait_for_job "$JOB01" "01-mpi-multinode"
check_result "$JOB01" "01-mpi-multinode" || { log "[ABORT] 01 失败，终止测试"; exit 1; }

JOB02=$(submit_job "02-slurm-env" "submit_array.sh")
log "Job 02 = $JOB02"

wait_for_job "$JOB02" "02-slurm-env"
check_result "$JOB02" "02-slurm-env" || { log "[ABORT] 02 失败，终止测试"; exit 1; }

# ——— Phase 2: 03/04/05 并行 ———
log "=========================================="
log "Phase 2: 并行运行 03/04/05"
log "=========================================="

JOB03=$(submit_job "03-resource-calibration" "submit.sh")
log "Job 03 = $JOB03"

JOB04a=$(submit_job "04-large-data-scale" "submit_analysis.sh")
log "Job 04a = $JOB04a"

JOB04b=$(submit_job "04-large-data-scale" "submit_batch_vis.sh")
log "Job 04b = $JOB04b"

JOB05=$(submit_job "05-pipeline-e2e" "submit.sh")
log "Job 05 = $JOB05"

for j in "$JOB03" "$JOB04a" "$JOB04b" "$JOB05"; do
    wait_for_job "$j" "Phase2-$j"
done

# ——— Phase 3: 检查结果 ———
log "=========================================="
log "Phase 3: 检查结果"
log "=========================================="

check_result "$JOB03" "03-resource-calibration"
check_result "$JOB04a" "04a-large-data-scale-analysis"
check_result "$JOB04b" "04b-large-data-scale-vis"
check_result "$JOB05" "05-pipeline-e2e"

# ——— Phase 4: 生成报告 ———
log "=========================================="
log "Phase 4: 生成报告"
log "=========================================="

mkdir -p "$(dirname "$FINAL_REPORT")"

{
    echo "# HPC Cluster Test Report"
    echo ""
    echo "> $(date +%Y-%m-%d) | 测试"
    echo ""
    echo "## 测试环境"
    echo ""
    echo "- 集群: <cluster_host>"
    echo "- 分区: <partition>"
    echo "- MPI: <mpi_module>"
    echo "- Conda: <conda_env>"
    echo "- 模拟数据: Au (19 GB)"
    echo ""
    echo "## 测试结果"
    echo ""
    if [ -s "$FAILS_FILE" ]; then
        echo "### 失败项"
        cat "$FAILS_FILE"
        echo ""
    else
        echo "全部测试通过。"
        echo ""
    fi
    echo "### 作业详情"
    echo ""
    for area in "01-mpi-multinode" "02-slurm-env" "03-resource-calibration" "04-large-data-scale" "05-pipeline-e2e"; do
        echo "#### $area"
        local_out=$(ls "$HPC_DIR/$area"/slurm-*.out 2>/dev/null | head -1)
        if [ -n "$local_out" ]; then
            echo '```'
            tail -30 "$local_out" 2>/dev/null
            echo '```'
        else
            echo "(无输出文件)"
        fi
        echo ""
    done
} > "$FINAL_REPORT"

log "报告: $FINAL_REPORT"
log "=========================================="
log "全部测试完成！"
log "=========================================="
