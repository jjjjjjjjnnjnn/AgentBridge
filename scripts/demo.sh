#!/usr/bin/env bash
# RelayOS Demo Script — 45-second walkthrough
# Run with: bash scripts/demo.sh
# Record with: terminalizer, vhs, or asciinema

set -e

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

DEMO_DIR="/tmp/relayos-demo"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║        RelayOS — AI Agent Operating System       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${DIM}Stop copy-pasting between AI tools.${NC}"
echo ""

sleep 1

# Step 1: Create terminals
echo -e "${BOLD}Step 1: Create persistent AI workers${NC}"
echo ""

echo -e "  ${CYAN}❯ relayos terminal create google -n researcher -m gemini-2.5-flash${NC}"
sleep 0.5
echo -e "  ${GREEN}✓${NC} Created 'researcher' (google/gemini-2.5-flash)"
echo ""

echo -e "  ${CYAN}❯ relayos terminal create anthropic -n architect -m claude-sonnet-4-20250514${NC}"
sleep 0.5
echo -e "  ${GREEN}✓${NC} Created 'architect' (anthropic/claude-sonnet)"
echo ""

echo -e "  ${CYAN}❯ relayos terminal create openai -n coder -m gpt-4o${NC}"
sleep 0.5
echo -e "  ${GREEN}✓${NC} Created 'coder' (openai/gpt-4o)"
echo ""

echo -e "  ${CYAN}❯ relayos terminal create deepseek -n reviewer${NC}"
sleep 0.5
echo -e "  ${GREEN}✓${NC} Created 'reviewer' (deepseek/deepseek-chat)"
echo ""

echo -e "  ${CYAN}❯ relayos terminal list${NC}"
sleep 0.3
echo -e "  ${DIM}ID          Name       Type      Model                         Status${NC}"
echo -e "  ${DIM}google-1    researcher google    gemini-2.5-flash              idle${NC}"
echo -e "  ${DIM}anthropic-1 architect  anthropic claude-sonnet-4-20250514      idle${NC}"
echo -e "  ${DIM}openai-1    coder      openai    gpt-4o                        idle${NC}"
echo -e "  ${DIM}deepseek-1  reviewer   deepseek  deepseek-chat                 idle${NC}"
echo ""
sleep 1.5

# Step 2: Create workflow file
echo -e "${BOLD}Step 2: Define a multi-agent workflow${NC}"
echo ""

cat > demo.yaml << 'EOF'
name: "SaaS Competitor Analysis"
steps:
  - agent: google
    prompt: "Research top 5 AI note-taking SaaS competitors. List their features, pricing, and gaps."
    save_as: research
    parallel: true

  - agent: anthropic
    prompt: "Design system architecture based on: {{research}}"
    save_as: architecture
    parallel: true

  - agent: openai
    prompt: "Implement core API from: {{architecture}}"
    save_as: code
    parallel: true

  - agent: deepseek
    prompt: "Review this code for security: {{code}}"
    save_as: review
EOF

echo -e "  ${DIM}Created demo.yaml with 4 steps${NC}"
echo ""
sleep 1

# Step 3: Run workflow
echo -e "${BOLD}Step 3: Run — one command, 4 agents collaborating${NC}"
echo ""

# Simulate animated execution
animate_step() {
  local agent="$1"
  local label="$2"
  local color="$3"
  local delay="$4"

  echo -ne "  ${color}⠋${NC} [${label}] $2..."
  sleep 0.5
  echo -ne "\r  ${color}⠙${NC} [${label}] $2..."
  sleep 0.5
  echo -ne "\r  ${color}⠹${NC} [${label}] $2..."
  sleep 0.3
  echo -ne "\r  ${color}⠸${NC} [${label}] $2..."
  sleep 0.3
  echo -ne "\r  ${color}⠼${NC} [${label}] $2..."
  sleep 0.5
  echo -e "\r  ${GREEN}✓${NC} [${label}] Done    ${DIM}(${delay})${NC}"
  sleep 0.5
}

# Run parallel first three
animate_step "google"    "researcher"  "$MAGENTA" "3.2s, 1,240 chars"
animate_step "anthropic" "architect"   "$BLUE"    "4.1s, 2,100 chars"
animate_step "openai"    "coder"       "$YELLOW"  "5.8s, 3,450 chars"

# Review step
echo ""
animate_step "deepseek"  "reviewer"    "$CYAN"    "2.3s, 890 chars"

# Step 4: Show results
echo ""
echo -e "${BOLD}Step 4: Results${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} ${BOLD}SaaS Competitor Analysis Complete${NC}"
echo -e "  ${DIM}  4 agents, 3 parallel steps, 1 review${NC}"
echo -e "  ${DIM}  Total: ~7,680 chars, ~15.4s execution${NC}"
echo ""
echo -e "  ${BOLD}Key findings saved to shared memory:${NC}"
echo -e "  ${DIM}  research     → competitive landscape (google)${NC}"
echo -e "  ${DIM}  architecture → system design (anthropic)${NC}"
echo -e "  ${DIM}  code         → API implementation (openai)${NC}"
echo -e "  ${DIM}  review       → security audit (deepseek)${NC}"
echo ""
sleep 1

# Final summary
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║    Without RelayOS: 4 copy-pastes, 15 min       ║${NC}"
echo -e "${BOLD}║    With RelayOS:    1 command, 15 seconds       ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Install:  pip install relayos${NC}"
echo -e "  ${CYAN}Docs:     github.com/jjjjjjjjnnjnn/relayos${NC}"
echo ""
