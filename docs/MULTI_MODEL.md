# Multi-Model Orchestration Guide

## Overview

Hrisa Code's multi-model orchestration system automatically selects the best model for each task, maximizing output quality by using specialized models where they excel.

## Architecture

The multi-model system consists of three main components:

### 1. Model Catalog (`model_catalog.py`)

Defines model profiles with:
- **Capabilities**: What the model is good at (code analysis, reasoning, documentation, etc.)
- **Quality Tier**: basic, good, excellent
- **Speed Tier**: fast, medium, slow
- **Parameter Count**: Model size (7B, 32B, 72B, 236B, etc.)
- **Strengths & Weaknesses**: Human-readable descriptions

**Supported Capabilities:**
- `FILE_OPERATIONS` - Basic file reading/listing
- `SIMPLE_SEARCH` - Simple file searches
- `PATTERN_GENERATION` - Generating regex/search patterns
- `CODE_ANALYSIS` - Understanding code structure
- `CODE_GENERATION` - Writing code
- `ARCHITECTURE_ANALYSIS` - Understanding system architecture
- `REASONING` - Logical reasoning
- `COMPLEX_REASONING` - Advanced multi-step reasoning
- `WORKFLOW_TRACING` - Tracing execution flows
- `TEXT_SYNTHESIS` - Generating coherent text
- `DOCUMENTATION_WRITING` - Writing documentation
- `TECHNICAL_WRITING` - Technical content creation

### 2. Model Router (`model_router.py`)

Intelligently routes tasks to appropriate models:
- Maps task types to required capabilities
- Selects best available model for each capability
- Implements graceful fallback when preferred models unavailable
- Supports custom selection strategies (prefer speed vs. quality)

**Task Types:**
- `ARCHITECTURE_DISCOVERY` → `ARCHITECTURE_ANALYSIS`
- `COMPONENT_ANALYSIS` → `CODE_ANALYSIS`
- `FEATURE_IDENTIFICATION` → `PATTERN_GENERATION`
- `WORKFLOW_UNDERSTANDING` → `WORKFLOW_TRACING`
- `DOCUMENTATION_SYNTHESIS` → `DOCUMENTATION_WRITING`

### 3. Conversation Manager Integration

- Supports dynamic model switching mid-conversation
- Preserves conversation history across model switches
- Displays model transitions to user

## Usage

### Basic Usage

```bash
# Standard single-model comprehensive generation
hrisa init --comprehensive --model qwen2.5-coder:32b

# Multi-model orchestration (uses best available model for each step)
hrisa init --comprehensive --multi-model
```

### What Happens During Multi-Model Orchestration

```
┌─────────────────────────────────────────────┐
│ Starting Orchestration                       │
│ Found 5 available models                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ► Model Selection                            │
│                                              │
│ Selected Model: qwen2.5:72b                  │
│                                              │
│ Reason: Strong reasoning, excellent          │
│ instruction following, good pattern          │
│ generation                                   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ► Orchestrator                               │
│                                              │
│ Step 1/5: Architecture Discovery             │
│                                              │
│ Exploring the codebase to understand         │
│ architecture...                              │
└─────────────────────────────────────────────┘

[... executes step with qwen2.5:72b ...]

┌─────────────────────────────────────────────┐
│ ► Model Selection                            │
│                                              │
│ Selected Model: deepseek-coder-v2:236b       │
│                                              │
│ Reason: Best-in-class code understanding,    │
│ excellent at tracing complex logic           │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ► Orchestrator                               │
│                                              │
│ Step 2/5: Component Analysis                 │
│                                              │
│ Exploring the codebase to understand         │
│ components...                                │
└─────────────────────────────────────────────┘

[... and so on for all 5 steps ...]
```

## Recommended Model Setup

For optimal multi-model orchestration, pull these models:

```bash
# 1. General reasoning and pattern generation
ollama pull qwen2.5:72b
# Size: ~47GB, Use for: architecture analysis, pattern generation

# 2. Deep code understanding
ollama pull deepseek-coder-v2:236b
# Size: ~133GB, Use for: component analysis, code understanding

# 3. Workflow tracing with reasoning
ollama pull deepseek-r1:70b
# Size: ~42GB, Use for: workflow tracing, complex reasoning

# 4. Documentation synthesis
ollama pull llama3.1:70b
# Size: ~40GB, Use for: writing comprehensive documentation

# Optional: Fast model for file operations
ollama pull qwen2.5-coder:7b
# Size: ~5GB, Use for: quick file operations (if needed)
```

**Total Download Size**: ~260GB for all recommended models

## Fallback Behavior

The system implements intelligent fallback:

1. **Best Model Available**: Uses highest-quality model with required capability
2. **Capability Fallback**: If no models with exact capability, uses best available model with related capabilities
3. **Default Fallback**: Uses configured default model (e.g., `qwen2.5-coder:32b`)
4. **Any Model Fallback**: Uses any available model as last resort

Example:
```
Required: WORKFLOW_TRACING
Preferred: deepseek-r1:70b

Fallback chain:
1. deepseek-r1:70b ✗ (not available)
2. llama3.1:70b ✓ (has REASONING capability)
   → Uses llama3.1:70b for this step
```

## Model Catalog

Current models in catalog:

### Fast Models (< 10B parameters)
- **qwen2.5-coder:7b** - Fast file operations, basic coding

### Medium Models (10-40B parameters)
- **qwen2.5-coder:32b** - Balanced coding, good instruction following
- **codestral:22b** - Mistral's coding specialist

### Large Models (70-100B parameters)
- **qwen2.5:72b** - Strong reasoning, pattern generation
- **llama3.1:70b** - Excellent prose, documentation writing
- **deepseek-r1:70b** - Chain-of-thought reasoning

### Massive Models (200B+ parameters)
- **deepseek-coder-v2:236b** - Best-in-class code understanding
- **llama3.1:405b** - Extremely capable for complex tasks
- **deepseek-r1:671b** - Research-level reasoning

## Customization

### Adding New Models

To add a custom model to the catalog:

```python
from hrisa_code.core.model_catalog import ModelCatalog, ModelProfile, ModelCapability, QualityTier, SpeedTier

catalog = ModelCatalog()
catalog.add_profile(ModelProfile(
    name="custom-model:70b",
    capabilities=[
        ModelCapability.CODE_ANALYSIS,
        ModelCapability.REASONING,
    ],
    quality_tier=QualityTier.EXCELLENT,
    speed_tier=SpeedTier.SLOW,
    strengths="Custom model optimized for specific tasks",
    parameter_count="70B",
    recommended_for=["custom_task_type"]
))
```

### Custom Selection Strategy

```python
from hrisa_code.core.model_router import ModelRouter, ModelSelectionStrategy

strategy = ModelSelectionStrategy(
    prefer_speed=True,  # Prefer faster models over quality
    allow_fallback=True,  # Allow fallback to available models
    available_models={"model1", "model2", "model3"},
    default_model="qwen2.5-coder:32b"
)

router = ModelRouter(strategy=strategy)
```

## Benefits

1. **Better Quality**: Specialized models for specialized tasks
2. **Optimal Resource Usage**: Use expensive models only where they add value
3. **Flexibility**: Works with whatever models you have available
4. **Transparency**: See which model is used for each step and why
5. **Future-Proof**: Easy to add new models as they become available

## Performance Considerations

### With Multi-Model
- **Quality**: ⭐⭐⭐⭐⭐ (Best model for each task)
- **Speed**: Varies by step (slow for complex steps, fast for simple steps)
- **VRAM**: Need enough for largest model (e.g., 140GB for 236B model)

### Without Multi-Model (Single Model)
- **Quality**: ⭐⭐⭐ (One model for all tasks)
- **Speed**: Consistent (same model throughout)
- **VRAM**: Only need enough for single model (e.g., 20GB for 32B model)

## Troubleshooting

### Models Not Switching

**Problem**: All steps use the same model

**Solution**:
1. Check models are actually pulled: `ollama list`
2. Verify `--multi-model` flag is used
3. Check `--comprehensive` is enabled (multi-model requires comprehensive mode)

### Model Not Found

**Problem**: Error about model not available

**Solution**: System will automatically fallback to available models. To use specific model, pull it first:
```bash
ollama pull model-name
```

### Out of Memory

**Problem**: System runs out of VRAM

**Solution**:
1. Use smaller models in catalog
2. Use prefer_speed strategy (prefers smaller models)
3. Pull only models your hardware can run

## Future Enhancements

- [ ] Model performance benchmarking
- [ ] Automatic model selection based on hardware
- [ ] Cost/time optimization
- [ ] Model caching for faster switching
- [ ] Sub-task level model selection (within a single step)

## See Also

- [FUTURE.md](../FUTURE.md) - Overall roadmap and future plans
- [README.md](../README.md) - Main documentation
- [model_catalog.py](../src/hrisa_code/core/model_catalog.py) - Model catalog implementation
- [model_router.py](../src/hrisa_code/core/model_router.py) - Model router implementation
