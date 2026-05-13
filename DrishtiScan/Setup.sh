#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# CropScan — JaivikDrishti AI
# One-command setup script
# Usage: bash setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit on any error

GREEN='\033[0;32m'
LIME='\033[1;32m'
DIM='\033[0;90m'
NC='\033[0m'  # No color
BOLD='\033[1m'

echo ""
echo -e "${LIME}${BOLD}╔════════════════════════════════════════════╗${NC}"
echo -e "${LIME}${BOLD}║   CropScan — JaivikDrishti AI Setup     ║${NC}"
echo -e "${LIME}${BOLD}╚════════════════════════════════════════════╝${NC}"
echo ""

# ── Check Python ─────────────────────────────────────────────────────────────
echo -e "${GREEN}[1/5]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+ from https://python.org"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "     ✅ Found: $PYTHON_VERSION"

# ── Create directories ────────────────────────────────────────────────────────
echo -e "${GREEN}[2/5]${NC} Creating project directories..."
mkdir -p model dataset logs frontend

echo "     ✅ Created: model/, dataset/, logs/, frontend/"

# ── Virtual environment ───────────────────────────────────────────────────────
echo -e "${GREEN}[3/5]${NC} Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "     ✅ Virtual environment created"
else
    echo "     ℹ️  Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# ── Install dependencies ──────────────────────────────────────────────────────
echo -e "${GREEN}[4/5]${NC} Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "     ✅ All dependencies installed"

# ── Create placeholder dataset structure ─────────────────────────────────────
echo -e "${GREEN}[5/5]${NC} Creating dataset placeholder structure..."

SAMPLE_CLASSES=(
    "Tomato___Early_blight"
    "Tomato___Late_blight"
    "Tomato___healthy"
    "Potato___Early_blight"
    "Potato___healthy"
    "Apple___Apple_scab"
    "Apple___healthy"
    "Corn_(maize)___Common_rust_"
    "Corn_(maize)___healthy"
)

for cls in "${SAMPLE_CLASSES[@]}"; do
    mkdir -p "dataset/$cls"
done

echo "     ✅ Created sample class directories in dataset/"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${LIME}${BOLD}════════════════════════════════════════════${NC}"
echo -e "${LIME}${BOLD}  Setup Complete! 🌿${NC}"
echo -e "${LIME}${BOLD}════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo ""
echo -e "  ${DIM}1.${NC} Add PlantVillage images to ${BOLD}dataset/${NC} folders"
echo -e "     Download from: https://www.kaggle.com/datasets/emmarex/plantdisease"
echo ""
echo -e "  ${DIM}2.${NC} Train the model:"
echo -e "     ${GREEN}python train.py --epochs 20${NC}"
echo ""
echo -e "  ${DIM}3.${NC} Start the API server:"
echo -e "     ${GREEN}uvicorn app.main:app --reload --port 8000${NC}"
echo ""
echo -e "  ${DIM}4.${NC} Open the frontend:"
echo -e "     ${GREEN}open frontend/index.html${NC}"
echo ""
echo -e "  ${DIM}5.${NC} View API docs:"
echo -e "     ${GREEN}http://localhost:8000/docs${NC}"
echo ""