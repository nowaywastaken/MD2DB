#!/bin/bash
# API Testing Script for MD2DB Rust Server
#
# This script tests all API endpoints with example data.
# Make sure the server is running before executing this script.

BASE_URL="${BASE_URL:-http://localhost:8080}"

echo "================================"
echo "MD2DB API Integration Test Script"
echo "================================"
echo "Server: $BASE_URL"
echo ""

# Function to print section headers
print_header() {
    echo ""
    echo ">>> $1"
    echo ""
}

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"

    echo "Test: $name"
    echo "Request: $method $endpoint"

    if [ -n "$data" ]; then
        echo "Data: $data"
        response=$(curl -s -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -X "$method" "$BASE_URL$endpoint")
    fi

    echo "Response:"
    echo "$response" | json_pp 2>/dev/null || echo "$response"
    echo ""
}

# 1. Health Check
print_header "1. Health Check Endpoint"
test_endpoint "Health Check" "GET" "/health"

# 2. Root Endpoint (API Info)
print_header "2. Root Endpoint (API Information)"
test_endpoint "API Info" "GET" "/"

# 3. Parse Simple Markdown
print_header "3. Parse Simple Question"
simple_md='{"markdown": "# What is 2+2?\n\n* A. 3\n* B. 4\n* C. 5\n"}'
test_endpoint "Parse Simple" "POST" "/parse" "$simple_md"

# 4. Parse Multiple Questions
print_header "4. Parse Multiple Questions"
multi_md='{"markdown": "# Question 1\n\n* A. Option 1\n* B. Option 2\n\n# Question 2\n\n* C. Option 3\n* D. Option 4\n"}'
test_endpoint "Parse Multiple" "POST" "/parse" "$multi_md"

# 5. Parse with LaTeX
print_header "5. Parse Question with LaTeX"
latex_md='{"markdown": "# What is the derivative of $x^2$?\n\n* A. \$x\$\n* B. \$2x\$\n* C. \$3x\$\n"}'
test_endpoint "Parse with LaTeX" "POST" "/parse" "$latex_md"

# 6. Empty Markdown
print_header "6. Parse Empty Markdown"
empty_md='{"markdown": ""}'
test_endpoint "Parse Empty" "POST" "/parse" "$empty_md"

# 7. Invalid JSON
print_header "7. Invalid JSON (Should Return Error)"
echo "Test: Invalid JSON"
echo "Request: POST /parse"
response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{invalid json}" \
    "$BASE_URL/parse")
echo "Response: $response"
echo ""

# 8. 404 Not Found
print_header "8. Non-existent Endpoint (Should Return 404)"
test_endpoint "404 Test" "GET" "/nonexistent"

# 9. Parse ZIP with Test File (if available)
print_header "9. Parse ZIP File"
if [ -f "test.zip" ]; then
    echo "Test: Parse ZIP File"
    echo "Request: POST /parse-zip"
    response=$(curl -s -X POST \
        -F "file=@test.zip" \
        "$BASE_URL/parse-zip")
    echo "Response:"
    echo "$response" | json_pp 2>/dev/null || echo "$response"
else
    echo "Skipping: test.zip not found"
    echo "To test this endpoint, create a ZIP file with Markdown files:"
    echo "  zip test.zip question1.md question2.md"
fi
echo ""

# 10. Test Error Response - Missing File
print_header "10. Parse ZIP Without File (Should Return Error)"
echo "Test: Parse ZIP Without File"
echo "Request: POST /parse-zip"
response=$(curl -s -X POST \
    -F "other_field=value" \
    "$BASE_URL/parse-zip")
echo "Response:"
echo "$response" | json_pp 2>/dev/null || echo "$response"
echo ""

echo "================================"
echo "Testing Complete"
echo "================================"
