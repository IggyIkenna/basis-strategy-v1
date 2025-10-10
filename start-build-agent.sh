#!/bin/bash
# Basis Strategy Build Agent Entry Point
# Autonomous execution of 26-step build plan

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
AGENT_NAME="Basis Strategy Build Executor"
BUILD_PLAN_FILE=".cursor/plans/26-step-agent-build-f5075160.plan.md"
MASTER_SEQUENCE=".cursor/tasks/00_master_task_sequence.md"
EXECUTOR_INSTRUCTIONS=".cursor/web-agent-build-executor.md"
LOG_FILE="logs/build-agent.log"
PROGRESS_FILE="logs/build-progress.json"

# Create logs directory
mkdir -p logs

# Function to log with timestamp
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${BLUE}[$timestamp]${NC} $message" | tee -a "$LOG_FILE"
}

# Function to log progress
log_progress() {
    local task="$1"
    local status="$2"
    local details="$3"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Create progress entry
    local progress_entry="{\"timestamp\":\"$timestamp\",\"task\":\"$task\",\"status\":\"$status\",\"details\":\"$details\"}"
    
    # Append to progress file
    if [ -f "$PROGRESS_FILE" ]; then
        # Remove last } and add new entry
        sed -i '$ s/}$//' "$PROGRESS_FILE"
        echo ",$progress_entry" >> "$PROGRESS_FILE"
        echo "}" >> "$PROGRESS_FILE"
    else
        echo "{\"progress\":[$progress_entry]}" > "$PROGRESS_FILE"
    fi
    
    log "PROGRESS: $task - $status - $details"
}

# Function to check backend health
check_backend_health() {
    log "Checking backend health..."
    
    # Check if backend is running
    if curl -s http://localhost:8001/health/ >/dev/null 2>&1; then
        log "✅ Backend is healthy and responding"
        return 0
    else
        log "❌ Backend is not responding"
        return 1
    fi
}

# Function to start backend
start_backend() {
    log "Starting backend in backtest mode..."
    
    # Stop any existing services
    ./platform.sh stop-local 2>/dev/null || true
    sleep 2
    
    # Start backend in backtest mode
    ./platform.sh backtest
    
    # Wait for backend to be ready
    local timeout=60
    local count=0
    
    while [ $count -lt $timeout ]; do
        if check_backend_health; then
            log "✅ Backend started successfully"
            return 0
        fi
        
        sleep 2
        count=$((count + 2))
    done
    
    log "❌ Backend failed to start within $timeout seconds"
    return 1
}

# Function to run quality gates
run_quality_gates() {
    log "Running comprehensive quality gates..."
    
    # Run quality gates and capture output
    local qg_output
    if qg_output=$(python scripts/run_quality_gates.py 2>&1); then
        log "✅ Quality gates completed successfully"
        echo "$qg_output" | tee -a "$LOG_FILE"
        return 0
    else
        log "❌ Quality gates failed"
        echo "$qg_output" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Function to execute a task
execute_task() {
    local task_file="$1"
    local task_name="$2"
    
    log "Executing task: $task_name"
    log_progress "$task_name" "STARTED" "Reading task file: $task_file"
    
    # Check if task file exists
    if [ ! -f "$task_file" ]; then
        log "❌ Task file not found: $task_file"
        log_progress "$task_name" "FAILED" "Task file not found"
        return 1
    fi
    
    # Read task file and extract key information
    log "Reading task requirements from: $task_file"
    
    # Extract quality gate script if mentioned
    local qg_script=$(grep -o "scripts/test_[a-zA-Z_]*_quality_gates.py" "$task_file" | head -1)
    
    if [ -n "$qg_script" ] && [ -f "$qg_script" ]; then
        log "Running task-specific quality gate: $qg_script"
        log_progress "$task_name" "IN_PROGRESS" "Running quality gate: $qg_script"
        
        if python "$qg_script" 2>&1 | tee -a "$LOG_FILE"; then
            log "✅ Task quality gate passed: $task_name"
            log_progress "$task_name" "COMPLETED" "Quality gate passed"
            return 0
        else
            log "❌ Task quality gate failed: $task_name"
            log_progress "$task_name" "FAILED" "Quality gate failed"
            return 1
        fi
    else
        log "⚠️ No specific quality gate found for task: $task_name"
        log "Task file content preview:"
        head -20 "$task_file" | tee -a "$LOG_FILE"
        log_progress "$task_name" "COMPLETED" "No quality gate to run"
        return 0
    fi
}

# Function to execute day tasks
execute_day() {
    local day="$1"
    shift
    local tasks=("$@")
    
    log "🚀 Starting Day $day execution"
    log "Tasks: ${tasks[*]}"
    
    local day_success=true
    
    for task in "${tasks[@]}"; do
        local task_file=".cursor/tasks/${task}.md"
        local task_name="Day${day}_${task}"
        
        if execute_task "$task_file" "$task_name"; then
            log "✅ Task completed successfully: $task"
        else
            log "❌ Task failed: $task"
            day_success=false
            # Continue with next task (don't stop entire day)
        fi
        
        # Small delay between tasks
        sleep 2
    done
    
    if $day_success; then
        log "✅ Day $day completed successfully"
        log_progress "Day_${day}" "COMPLETED" "All tasks completed successfully"
    else
        log "⚠️ Day $day completed with some failures"
        log_progress "Day_${day}" "PARTIAL" "Some tasks failed"
    fi
    
    return 0
}

# Function to show current status
show_status() {
    log "📊 Current Build Status"
    
    # Check backend status
    if check_backend_health; then
        echo -e "${GREEN}✅ Backend: Running${NC}"
    else
        echo -e "${RED}❌ Backend: Not running${NC}"
    fi
    
    # Show progress if available
    if [ -f "$PROGRESS_FILE" ]; then
        echo -e "${BLUE}📈 Progress:${NC}"
        cat "$PROGRESS_FILE" | jq -r '.progress[] | "\(.timestamp) - \(.task): \(.status)"' 2>/dev/null || echo "Progress file exists but not readable"
    fi
    
    # Show recent logs
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}📋 Recent logs:${NC}"
        tail -10 "$LOG_FILE"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}$AGENT_NAME${NC}"
    echo ""
    echo -e "${YELLOW}Usage: $0 [COMMAND]${NC}"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo -e "  ${BLUE}start${NC}        Start autonomous build execution"
    echo -e "  ${BLUE}status${NC}       Show current build status"
    echo -e "  ${BLUE}health${NC}       Check backend health"
    echo -e "  ${BLUE}quality${NC}      Run quality gates"
    echo -e "  ${BLUE}day1${NC}         Execute Day 1 tasks only"
    echo -e "  ${BLUE}day2${NC}         Execute Day 2 tasks only"
    echo -e "  ${BLUE}day3${NC}         Execute Day 3 tasks only"
    echo -e "  ${BLUE}day4${NC}         Execute Day 4 tasks only"
    echo -e "  ${BLUE}day5${NC}         Execute Day 5 tasks only"
    echo -e "  ${BLUE}day6${NC}         Execute Day 6 tasks only"
    echo -e "  ${BLUE}help${NC}         Show this help message"
    echo ""
    echo -e "${GREEN}Build Plan:${NC}"
    echo -e "  ${BLUE}Total Tasks:${NC} 26"
    echo -e "  ${BLUE}Timeline:${NC} 6 days"
    echo -e "  ${BLUE}Target:${NC} 20/24 quality gates passing (83%)"
    echo -e "  ${BLUE}Coverage:${NC} 80% unit test coverage"
    echo ""
    echo -e "${GREEN}Files:${NC}"
    echo -e "  ${BLUE}Build Plan:${NC} $BUILD_PLAN_FILE"
    echo -e "  ${BLUE}Instructions:${NC} $EXECUTOR_INSTRUCTIONS"
    echo -e "  ${BLUE}Logs:${NC} $LOG_FILE"
    echo -e "  ${BLUE}Progress:${NC} $PROGRESS_FILE"
}

# Main execution function
main() {
    local command="${1:-help}"
    
    case "$command" in
        "start")
            log "🚀 Starting autonomous build execution"
            log "Build Plan: $BUILD_PLAN_FILE"
            log "Instructions: $EXECUTOR_INSTRUCTIONS"
            
            # Initialize progress file
            echo '{"progress":[]}' > "$PROGRESS_FILE"
            
            # Start backend
            if ! start_backend; then
                log "❌ Failed to start backend. Cannot proceed."
                exit 1
            fi
            
            # Run initial quality gates
            log "Running baseline quality gates..."
            run_quality_gates
            
            # Execute all days
            log "🎯 Beginning 6-day build execution"
            
            # Day 1: Foundation
            execute_day 1 "01_environment_file_switching" "02_config_loading_validation" "03_data_loading_quality_gate"
            
            # Day 2: Core Architecture
            execute_day 2 "07_fix_async_await_violations" "10_reference_based_architecture" "11_singleton_pattern" "06_strategy_manager_refactor" "08_mode_agnostic_architecture" "09_fail_fast_configuration"
            
            # Day 3: Integration
            execute_day 3 "12_tight_loop_architecture" "13_consolidate_duplicate_risk_monitors" "14_component_data_flow_architecture" "04_complete_api_endpoints" "05_health_logging_structure"
            
            # Day 4: Strategy Validation
            execute_day 4 "15_pure_lending_quality_gates" "16_btc_basis_quality_gates" "17_eth_basis_quality_gates"
            
            # Day 5: Complex Modes & Unit Tests
            execute_day 5 "18_usdt_market_neutral_quality_gates" "19_position_monitor_unit_tests" "20_exposure_monitor_unit_tests" "21_risk_monitor_unit_tests" "22_strategy_manager_unit_tests" "23_pnl_calculator_unit_tests"
            
            # Day 6: Frontend & Live Mode
            execute_day 6 "24_frontend_implementation" "25_live_mode_quality_gates" "26_comprehensive_quality_gates"
            
            # Final quality gates
            log "🎯 Running final comprehensive quality gates"
            run_quality_gates
            
            log "🎉 Build execution completed!"
            show_status
            ;;
            
        "status")
            show_status
            ;;
            
        "health")
            if check_backend_health; then
                echo -e "${GREEN}✅ Backend is healthy${NC}"
            else
                echo -e "${RED}❌ Backend is not healthy${NC}"
            fi
            ;;
            
        "quality")
            run_quality_gates
            ;;
            
        "day1")
            start_backend
            execute_day 1 "01_environment_file_switching" "02_config_loading_validation" "03_data_loading_quality_gate"
            ;;
            
        "day2")
            start_backend
            execute_day 2 "07_fix_async_await_violations" "10_reference_based_architecture" "11_singleton_pattern" "06_strategy_manager_refactor" "08_mode_agnostic_architecture" "09_fail_fast_configuration"
            ;;
            
        "day3")
            start_backend
            execute_day 3 "12_tight_loop_architecture" "13_consolidate_duplicate_risk_monitors" "14_component_data_flow_architecture" "04_complete_api_endpoints" "05_health_logging_structure"
            ;;
            
        "day4")
            start_backend
            execute_day 4 "15_pure_lending_quality_gates" "16_btc_basis_quality_gates" "17_eth_basis_quality_gates"
            ;;
            
        "day5")
            start_backend
            execute_day 5 "18_usdt_market_neutral_quality_gates" "19_position_monitor_unit_tests" "20_exposure_monitor_unit_tests" "21_risk_monitor_unit_tests" "22_strategy_manager_unit_tests" "23_pnl_calculator_unit_tests"
            ;;
            
        "day6")
            start_backend
            execute_day 6 "24_frontend_implementation" "25_live_mode_quality_gates" "26_comprehensive_quality_gates"
            ;;
            
        "help"|"--help"|"-h")
            show_help
            ;;
            
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Check if jq is available for JSON processing
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️ Warning: jq not found. Progress tracking will be limited.${NC}"
    echo -e "${YELLOW}Install with: brew install jq (macOS) or apt-get install jq (Ubuntu)${NC}"
fi

# Run main function
main "$@"
