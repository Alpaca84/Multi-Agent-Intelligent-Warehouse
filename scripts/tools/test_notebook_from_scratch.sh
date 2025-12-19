#!/bin/bash
# Test notebook from scratch - simulates new user experience

set -e

TEST_DIR="$HOME/test-warehouse-notebook-$(date +%s)"
REPO_NAME="Multi-Agent-Intelligent-Warehouse"

echo "🧪 Testing Notebook from Scratch"
echo "=" * 60
echo ""
echo "This script will:"
echo "  1. Create a clean test directory: $TEST_DIR"
echo "  2. Start Jupyter in that directory (repo not cloned yet)"
echo "  3. You can then test the notebook step-by-step"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Create test directory
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo ""
echo "✅ Created test directory: $TEST_DIR"
echo ""

# Create a minimal venv for Jupyter
echo "📦 Setting up Jupyter environment..."
python3 -m venv test-jupyter-env
source test-jupyter-env/bin/activate
pip install -q jupyter ipykernel
python -m ipykernel install --user --name=test-warehouse-jupyter

echo "✅ Jupyter environment ready"
echo ""
echo "📋 Next steps:"
echo "  1. Jupyter will start in: $TEST_DIR"
echo "  2. Open: notebooks/setup/complete_setup_guide.ipynb"
echo "  3. In Step 2, uncomment the cloning code to test automatic cloning"
echo "  4. Or clone manually: git clone https://github.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse.git"
echo "  5. Follow the notebook step-by-step"
echo ""
echo "🚀 Starting Jupyter..."
echo ""

# Copy notebook to test directory (so it can be opened)
# Actually, we need to clone first or download the notebook
echo "📥 Downloading notebook..."
mkdir -p notebooks/setup
curl -s https://raw.githubusercontent.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse/main/notebooks/setup/complete_setup_guide.ipynb -o notebooks/setup/complete_setup_guide.ipynb || {
    echo "⚠️  Could not download notebook. You'll need to clone the repo first."
    echo "   Run: git clone https://github.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse.git"
}

jupyter notebook notebooks/setup/complete_setup_guide.ipynb
