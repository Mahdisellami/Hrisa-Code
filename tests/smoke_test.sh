#!/bin/bash
# Quick smoke test to verify basic functionality after multi-model implementation

set -e  # Exit on error

cd "$(dirname "$0")/.."  # Go to project root
source venv/bin/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true

echo "=== HRISA CODE SMOKE TEST ==="
echo "Testing basic functionality after multi-model implementation"
echo ""

# Test 1: Python imports
echo "1. Testing Python imports..."
python3 << 'EOF'
try:
    from hrisa_code.core.config import Config
    from hrisa_code.core.conversation import OllamaClient, OllamaConfig, ConversationManager
    from hrisa_code.core.interface import InteractiveSession
    from hrisa_code.core.orchestrators import HrisaOrchestrator
    from hrisa_code.core.model_catalog import ModelCatalog, ModelProfile, ModelCapability
    from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy
    from hrisa_code.tools.file_operations import AVAILABLE_TOOLS
    print("   ✓ All imports successful")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    exit(1)
EOF

# Test 2: CLI entry point
echo ""
echo "2. Testing CLI entry point..."
if hrisa --version > /dev/null 2>&1; then
    VERSION=$(hrisa --version 2>&1 | grep -o "version.*")
    echo "   ✓ CLI works ($VERSION)"
else
    echo "   ✗ CLI failed"
    exit 1
fi

# Test 3: Model catalog
echo ""
echo "3. Testing model catalog..."
python3 << 'EOF'
try:
    from hrisa_code.core.model_catalog import ModelCatalog, ModelCapability
    catalog = ModelCatalog()
    model_count = len(catalog.list_all_models())
    code_models = catalog.get_models_by_capability(ModelCapability.CODE_ANALYSIS)
    print(f"   ✓ Catalog has {model_count} models, {len(code_models)} with CODE_ANALYSIS")
except Exception as e:
    print(f"   ✗ Catalog failed: {e}")
    exit(1)
EOF

# Test 4: Model router
echo ""
echo "4. Testing model router..."
python3 << 'EOF'
try:
    from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy, TaskType
    strategy = ModelSelectionStrategy(
        available_models={"qwen2.5-coder:32b"},
        default_model="qwen2.5-coder:32b"
    )
    router = ModelRouter(strategy=strategy)
    model = router.select_model_for_task(TaskType.CODE_ANALYSIS)
    print(f"   ✓ Router works (selected: {model})")
except Exception as e:
    print(f"   ✗ Router failed: {e}")
    exit(1)
EOF

# Test 5: Model switching
echo ""
echo "5. Testing model switching..."
python3 << 'EOF'
try:
    from hrisa_code.core.conversation import OllamaClient, OllamaConfig
    config = OllamaConfig(model="model1")
    client = OllamaClient(config)

    assert client.get_current_model() == "model1", "Initial model wrong"
    client.switch_model("model2")
    assert client.get_current_model() == "model2", "Switch failed"
    print("   ✓ Model switching works")
except Exception as e:
    print(f"   ✗ Model switching failed: {e}")
    exit(1)
EOF

# Test 6: Models command (requires Ollama running)
echo ""
echo "6. Testing models command..."
if hrisa models --help > /dev/null 2>&1; then
    echo "   ✓ Models command exists"
else
    echo "   ✗ Models command failed"
    exit 1
fi

# Test 7: Init command (dry run)
echo ""
echo "7. Testing init command..."
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
if hrisa init --skip-hrisa --force > /dev/null 2>&1; then
    if [ -f .hrisa/config.yaml ]; then
        echo "   ✓ Init command works"
    else
        echo "   ✗ Init command didn't create config"
        cd - > /dev/null
        rm -rf "$TEST_DIR"
        exit 1
    fi
else
    echo "   ✗ Init command failed"
    cd - > /dev/null
    rm -rf "$TEST_DIR"
    exit 1
fi
cd - > /dev/null
rm -rf "$TEST_DIR"

# Test 8: Chat command (check it exists)
echo ""
echo "8. Testing chat command..."
if hrisa chat --help > /dev/null 2>&1; then
    echo "   ✓ Chat command exists"
else
    echo "   ✗ Chat command failed"
    exit 1
fi

# Test 9: Orchestrator instantiation
echo ""
echo "9. Testing orchestrator..."
python3 << 'EOF'
try:
    from hrisa_code.core.orchestrators import HrisaOrchestrator
    from hrisa_code.core.conversation import ConversationManager, OllamaConfig
    from hrisa_code.core.model_router import ModelRouter
    from pathlib import Path

    config = OllamaConfig(model="test")
    conversation = ConversationManager(
        ollama_config=config,
        working_directory=Path.cwd(),
        enable_tools=False
    )

    # Test without multi-model
    orch1 = HrisaOrchestrator(
        conversation=conversation,
        project_path=Path.cwd()
    )
    assert orch1.enable_multi_model == False, "Default should be False"

    # Test with multi-model
    router = ModelRouter()
    orch2 = HrisaOrchestrator(
        conversation=conversation,
        project_path=Path.cwd(),
        model_router=router,
        enable_multi_model=True
    )
    assert orch2.enable_multi_model == True, "Should be True"
    assert orch2.model_router is not None, "Router should be set"

    print("   ✓ Orchestrator instantiation works")
except Exception as e:
    print(f"   ✗ Orchestrator failed: {e}")
    exit(1)
EOF

# Test 10: Backward compatibility
echo ""
echo "10. Testing backward compatibility..."
python3 << 'EOF'
try:
    # Old code should still work without changes
    from hrisa_code.core.conversation import OllamaConfig, ConversationManager
    from pathlib import Path

    # This is how old code created conversation managers
    config = OllamaConfig(model="test")
    conversation = ConversationManager(
        ollama_config=config,
        working_directory=Path.cwd(),
        enable_tools=True
    )

    # Old methods should still exist
    assert hasattr(conversation, 'clear_history'), "Missing clear_history"
    assert hasattr(conversation, 'save_conversation'), "Missing save_conversation"
    assert hasattr(conversation, 'load_conversation'), "Missing load_conversation"

    # New methods should be added
    assert hasattr(conversation, 'switch_model'), "Missing switch_model"
    assert hasattr(conversation, 'get_current_model'), "Missing get_current_model"

    print("   ✓ Backward compatibility maintained")
except Exception as e:
    print(f"   ✗ Compatibility check failed: {e}")
    exit(1)
EOF

echo ""
echo "=== SMOKE TEST COMPLETE ==="
echo ""
echo "✓ All 10 tests passed!"
echo "✓ Basic functionality is intact"
echo "✓ New multi-model features added without breaking existing code"
echo ""
echo "You can now run comprehensive tests in tests/REGRESSION_TESTS.md"
