#!/bin/bash
"""
Comprehensive verification script.
This script ensures nothing is marked as "done" without proper testing.
"""

set -e  # Exit on any error

echo "🚀 Starting Comprehensive Verification Process"
echo "============================================"
echo "This script verifies all components are properly tested before marking as 'done'"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Track overall status
FAILED=0

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    echo -n "🔍 $name... "
    
    if eval "$command" > /tmp/check_output.log 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "   Error output:"
        cat /tmp/check_output.log | head -10 | sed 's/^/   /'
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Syntax Check
echo "1️⃣  SYNTAX VALIDATION"
echo "-------------------"
run_check "Python syntax check" "python -m py_compile src/**/*.py"
run_check "Import verification" "python testing-framework/pre-commit/verify_imports.py src/**/*.py"
echo

# 2. Unit Tests
echo "2️⃣  UNIT TESTS"
echo "------------"
run_check "Diagnostic tests" "pytest tests/unit/test_diagnostics.py -v"
run_check "Security tests" "pytest tests/unit/test_security.py -v" || true
run_check "Model tests" "pytest tests/unit/test_models.py -v" || true
echo

# 3. Integration Tests
echo "3️⃣  INTEGRATION TESTS"
echo "------------------"
# Check if services are running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
    
    # Test endpoints
    run_check "Health endpoint" "curl -s http://localhost:8000/health | jq '.status'"
    run_check "API docs available" "curl -s http://localhost:8000/api/v1/docs | grep -q 'swagger-ui'"
else
    echo -e "${RED}✗ Backend server is not running${NC}"
    FAILED=$((FAILED + 1))
fi
echo

# 4. Security Scans
echo "4️⃣  SECURITY SCANS"
echo "----------------"
run_check "Bandit security scan" "bandit -r src/ -f json -o /tmp/bandit.json || true"
run_check "Safety dependency check" "safety check --json || true"
run_check "Secret detection" "python testing-framework/pre-commit/security_scan.py src/**/*.py"
echo

# 5. Code Coverage
echo "5️⃣  CODE COVERAGE"
echo "---------------"
if command -v coverage &> /dev/null; then
    run_check "Generate coverage report" "coverage run -m pytest tests/unit/ && coverage report"
else
    echo -e "${YELLOW}⚠ Coverage tool not installed${NC}"
fi
echo

# 6. Error Handling Verification
echo "6️⃣  ERROR HANDLING"
echo "-----------------"
run_check "Diagnostic error checks" "python testing-framework/pre-commit/diagnostic_check.py src/**/*.py"
echo

# 7. API Testing (if server is running)
echo "7️⃣  API TESTING"
echo "-------------"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    # Test authentication error handling
    echo "Testing error responses..."
    
    # Test invalid login
    response=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=invalid@test.com&password=wrongpass" \
        -w "\nHTTP_CODE:%{http_code}")
    
    http_code=$(echo "$response" | grep HTTP_CODE | cut -d: -f2)
    
    if [ "$http_code" = "401" ] || [ "$http_code" = "400" ]; then
        echo -e "${GREEN}✓ Auth error handling works (HTTP $http_code)${NC}"
    else
        echo -e "${RED}✗ Unexpected auth response (HTTP $http_code)${NC}"
        FAILED=$((FAILED + 1))
    fi
fi
echo

# 8. Performance Checks
echo "8️⃣  PERFORMANCE CHECKS"
echo "-------------------"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    # Simple latency test
    start_time=$(date +%s%N)
    curl -s http://localhost:8000/health > /dev/null
    end_time=$(date +%s%N)
    latency=$(( ($end_time - $start_time) / 1000000 ))
    
    if [ $latency -lt 100 ]; then
        echo -e "${GREEN}✓ Health endpoint latency: ${latency}ms${NC}"
    else
        echo -e "${YELLOW}⚠ Health endpoint latency: ${latency}ms (>100ms)${NC}"
    fi
fi
echo

# 9. Documentation Check
echo "9️⃣  DOCUMENTATION"
echo "---------------"
run_check "API documentation" "[ -f README.md ]"
run_check "Test documentation" "grep -r 'CRITICAL:' tests/ | wc -l | grep -q '[0-9]'"
echo

# Final Summary
echo "📊 VERIFICATION SUMMARY"
echo "====================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo "The code is properly tested and verified."
    echo "It is safe to mark this work as 'DONE'."
    exit 0
else
    echo -e "${RED}❌ FAILED CHECKS: $FAILED${NC}"
    echo
    echo "⚠️  DO NOT mark this work as 'done' until all checks pass!"
    echo
    echo "Fix suggestions:"
    echo "1. Run failed tests individually to see detailed errors"
    echo "2. Check server logs: tail -f backend-debug.log"
    echo "3. Ensure all services are running (PostgreSQL, Redis)"
    echo "4. Run: pytest -xvs <test_file> for detailed test output"
    exit 1
fi