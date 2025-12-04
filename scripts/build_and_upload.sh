#!/bin/bash

##########################################################################
##                                                                      ##
##  FEDI Package Build and Upload Script                                ##
##                                                                      ##
##  This script automates the process of building and uploading the     ##
##  FEDI package to PyPI. Run this before pushing changes to the main   ##
##  repository.                                                         ##
##                                                                      ##
##  Usage:                                                              ##
##    ./scripts/build_and_upload.sh [--test] [--no-upload]              ##
##                                                                      ##
##  Options:                                                            ##
##    --test       Upload to TestPyPI instead of PyPI                  ##
##    --no-upload  Build only, do not upload (useful for testing)        ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)       ##
##                                                                      ##
##########################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command-line arguments
TEST_PYPI=false
NO_UPLOAD=false

for arg in "$@"; do
    case $arg in
        --test)
            TEST_PYPI=true
            shift
            ;;
        --no-upload)
            NO_UPLOAD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--test] [--no-upload]"
            echo ""
            echo "Options:"
            echo "  --test       Upload to TestPyPI instead of PyPI"
            echo "  --no-upload  Build only, do not upload"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $arg${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FEDI Package Build and Upload${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if required tools are installed
echo -e "${YELLOW}Checking required tools...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command -v twine &> /dev/null; then
    echo -e "${RED}Error: twine is not installed. Install it with: pip install twine${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $(python3 --version)"

# Get current version from setup.py
CURRENT_VERSION=$(grep -E "^\s*version\s*=" setup.py | sed -E "s/.*version\s*=\s*['\"]([^'\"]+)['\"].*/\1/")
echo -e "${GREEN}Current version: ${CURRENT_VERSION}${NC}"
echo ""

# Step 1: Clean previous build artifacts
echo -e "${YELLOW}Step 1: Cleaning previous build artifacts...${NC}"
rm -rf build dist *.egg-info
echo -e "${GREEN}✓ Cleaned build artifacts${NC}"
echo ""

# Step 2: Verify version consistency
echo -e "${YELLOW}Step 2: Verifying version consistency...${NC}"
if [ -f "FEDI/__init__.py" ]; then
    INIT_VERSION=$(grep -E "^__version__\s*=" FEDI/__init__.py | sed -E "s/.*__version__\s*=\s*['\"]([^'\"]+)['\"].*/\1/" || echo "")
    if [ -n "$INIT_VERSION" ] && [ "$INIT_VERSION" != "$CURRENT_VERSION" ]; then
        echo -e "${YELLOW}Warning: Version mismatch detected!${NC}"
        echo "  setup.py version: $CURRENT_VERSION"
        echo "  FEDI/__init__.py version: $INIT_VERSION"
        echo -e "${YELLOW}Consider updating both to match.${NC}"
    else
        echo -e "${GREEN}✓ Version consistency verified${NC}"
    fi
fi
echo ""

# Step 3: Build the package
echo -e "${YELLOW}Step 3: Building package (source distribution and wheel)...${NC}"
python3 setup.py sdist bdist_wheel

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build completed successfully${NC}"
echo ""

# Step 4: Check package contents
echo -e "${YELLOW}Step 4: Checking package contents...${NC}"
python3 -m twine check dist/*

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Package check failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Package check passed${NC}"
echo ""

# Step 5: Upload to PyPI
if [ "$NO_UPLOAD" = true ]; then
    echo -e "${YELLOW}Skipping upload (--no-upload flag set)${NC}"
    echo -e "${GREEN}Package built successfully in dist/ directory${NC}"
    echo ""
    echo "To upload manually, run:"
    if [ "$TEST_PYPI" = true ]; then
        echo "  twine upload --repository testpypi dist/*"
    else
        echo "  twine upload dist/*"
    fi
else
    echo -e "${YELLOW}Step 5: Uploading to PyPI...${NC}"
    
    if [ "$TEST_PYPI" = true ]; then
        echo -e "${YELLOW}Uploading to TestPyPI...${NC}"
        python3 -m twine upload --repository testpypi dist/*
    else
        echo -e "${YELLOW}Uploading to PyPI (production)...${NC}"
        echo -e "${RED}WARNING: This will upload to the production PyPI repository!${NC}"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo -e "${YELLOW}Upload cancelled${NC}"
            exit 0
        fi
        
        python3 -m twine upload dist/*
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Upload failed!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Upload completed successfully${NC}"
    echo ""
    
    if [ "$TEST_PYPI" = true ]; then
        echo -e "${GREEN}Package uploaded to TestPyPI${NC}"
        echo "Test installation with:"
        echo "  pip install --index-url https://test.pypi.org/simple/ fedi"
    else
        echo -e "${GREEN}Package uploaded to PyPI${NC}"
        echo "Users can now install with:"
        echo "  pip install fedi"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build and upload process completed!${NC}"
echo -e "${GREEN}========================================${NC}"

