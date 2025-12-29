# Progressive Orchestration Test Results

**Date**: December 29, 2025
**Test Duration**: ~3 hours
**Models Tested**: qwen2.5-coder:32b, qwen2.5:72b

## Executive Summary

Progressive orchestration was implemented and tested with two models. Results show that **the approach has fundamental prompt design issues** that prevent production-quality documentation generation, regardless of model size.

## Test Setup

### What We Tested

Created 4 progressive orchestrators:
1. `ProgressiveReadmeOrchestrator` - User-facing project documentation
2. `ProgressiveApiOrchestrator` - API reference documentation
3. `ProgressiveContributingOrchestrator` - Contributor guidelines
4. `ProgressiveHrisaOrchestrator` - AI assistant-focused documentation

Each orchestrator follows the same pattern:
- **Phase 1**: Extract facts from pyproject.toml (validated)
- **Phase 2**: Build title section (direct template, no LLM)
- **Phases 3-6**: Build content sections (code-based discovery, validated)
- **Phase 7**: Assemble final document (simple concatenation)

### Models Used

1. **qwen2.5-coder:32b** - Smaller coding-focused model
2. **qwen2.5:72b** - Larger general-purpose reasoning model

## Test Results

### qwen2.5-coder:32b Results

| Document | Lines | Size | Time | Quality | Issues |
|----------|-------|------|------|---------|--------|
| README | 51 | 2.3K | ~5min | ❌ FAIL | Tool leaks, hallucinations, wrong features |
| API | 453 | 19K | ~10min | ⚠️ POOR | Massive tool leak (entire config.py dumped) |
| CONTRIBUTING | 325 | 7.9K | ~10min | ⚠️ POOR | Multiple issues |
| HRISA | 165 | 7.8K | ~8min | ⚠️ POOR | Tool call leaks (2 instances) |

**Key Issues**:
- **Tool Call Leakage**: JSON artifacts leaked into all documents
- **Severe Hallucinations**: Invented CLI commands that don't exist
- **Wrong Content**: README discussed venv directory instead of project
- **Incomplete**: All documents significantly shorter than needed

### qwen2.5:72b Results

| Document | Lines | Size | Time | Quality | Issues |
|----------|-------|------|------|---------|--------|
| README | 119 | 3.8K | ~37min | ⚠️ POOR | Wrong features, conversational, asks for input |
| API | 232 | 10K | ~68min | ⚠️ POOR | Conversational explanations |
| CONTRIBUTING | 143 | 4.5K | ~48min | ⚠️ POOR | Conversational instead of directive |
| HRISA | 289 | 12K | ~56min | ⚠️ POOR | Meta-commentary |

**Key Issues**:
- **Wrong Features**: Listed "init", "serve", "generate", "lint", "test" - none of which exist as CLI commands
- **Conversational Tone**: Documents read like AI responses ("It looks like...", "Here are some key points...")
- **Asks for Input**: README line 109: "Could you please provide a list of those commands?"
- **Very Slow**: Average 52 minutes per document (vs ~8min with 32b)

### Comparison to Original Documentation

| Document | Original Lines | 32b Lines | 72b Lines | Quality Loss |
|----------|---------------|-----------|-----------|--------------|
| README | 566 | 51 (91% smaller) | 119 (79% smaller) | Severe |
| API | ~500 (est) | 453 | 232 (54% smaller) | Severe |
| CONTRIBUTING | 326 | 325 | 143 (56% smaller) | Severe |
| HRISA (vs CLAUDE.md) | 480 | 165 (66% smaller) | 289 (40% smaller) | Severe |

## Root Cause Analysis

### Why Progressive Orchestration Failed

1. **Prompt Design Issues**
   - Prompts are too conversational ("Task: Document...", "Your job: Discover...")
   - Models interpret these as chat conversations, not documentation tasks
   - Result: Conversational responses instead of clean documentation

2. **Discovery Phase Problems**
   - Phase 3 (Features) fails to correctly identify CLI commands
   - Models either hallucinate commands or miss actual ones
   - Tool-based discovery doesn't work reliably

3. **Validation Not Effective**
   - Regex validation only checks if project name appears
   - Doesn't validate actual content quality or accuracy
   - False sense of correctness

4. **Assembly Issues**
   - Simple concatenation preserves all problems from earlier phases
   - No final quality check or cleanup step

### Specific Examples

**README with 72b - Wrong Features**:
```markdown
## Features

- **init**: Initialize a new project with configuration files.
- **serve**: Start the local development server for testing and debugging.
- **generate**: Generate code snippets or entire modules based on templates.
```

Reality: These commands don't exist. Actual commands are: `chat`, `models`, `readme`, `api`, `contributing`, `hrisa`, etc.

**README with 72b - Conversational Content**:
```markdown
It looks like you've provided a detailed overview of the Hrisa Code project,
which is an open-source, locally-run coding assistant that leverages Ollama
for LLM inference. Here are some key points and features summarized:
```

This reads like an AI's response to a user, not documentation.

**README with 72b - Asks for Help**:
```markdown
To generate the usage section, I need to know which CLI commands were
discovered in Phase 3. Could you please provide a list of those commands
and their subcommands?
```

The model is asking the user for clarification!

## Performance Analysis

### Execution Time

| Model | Avg Time/Doc | Total Time (4 docs) |
|-------|--------------|---------------------|
| qwen2.5-coder:32b | ~8 min | ~32 min |
| qwen2.5:72b | ~52 min | ~208 min (3.5 hours) |

**Conclusion**: 72b model is 6.5x slower with marginal quality improvement.

### Quality vs Speed Tradeoff

- **32b**: Fast but produces garbage (tool leaks, severe hallucinations)
- **72b**: Slow but still produces poor quality (conversational, wrong features)
- **Neither**: Suitable for production use

## What Worked

1. **Code Structure**: The orchestrator architecture is clean and modular
2. **Phase Separation**: Breaking into phases is conceptually sound
3. **Direct Templates**: Phase 2 (title) works perfectly using direct templates
4. **Tool Integration**: File reading and tool execution works correctly
5. **CLI Integration**: Commands are properly integrated into Typer

## What Didn't Work

1. **Prompt Engineering**: Current prompts lead to conversational responses
2. **Feature Discovery**: Can't reliably identify actual CLI commands
3. **Content Quality**: Generated content is not documentation-grade
4. **Validation**: Regex checks don't catch quality issues
5. **Model Suitability**: Neither model can handle this task with current prompts

## Recommendations

### Immediate Actions

1. **Do Not Use Progressive Orchestrators in Production**
   - Current implementation produces subpar documentation
   - Risk of incorrect/misleading content

2. **Keep Old Orchestrators**
   - The original synthesis-based orchestrators, while not perfect, produced better results
   - Previous README had 566 lines of accurate content vs 119 lines of mixed quality

3. **Update Documentation**
   - Document that progressive approach needs refinement
   - Mark progressive commands as experimental

### Future Improvements

If continuing with progressive orchestration:

1. **Simplify Prompts**
   - Remove conversational language
   - Use directive statements: "Extract the following..." not "Your task is to..."
   - Provide exact output format templates

2. **Use Static Discovery**
   - Parse code directly with AST instead of asking LLM to discover
   - Extract CLI commands using Typer's introspection
   - Only use LLM for writing prose, not discovery

3. **Add Quality Validation**
   - Check for conversational phrases ("It looks like...", "Here are...")
   - Validate features against actual CLI commands
   - Reject output that asks questions

4. **Hybrid Approach**
   - Use progressive extraction for facts
   - Use templates for structure
   - Use LLM only for specific prose sections
   - Validate and filter each LLM output

5. **Better Model Selection**
   - Test with models specifically tuned for documentation (not coding)
   - Consider using Claude API for critical documentation (ironic but effective)

## Conclusion

The progressive orchestration experiment revealed that **breaking documentation into phases is conceptually sound, but the current prompt design and validation are insufficient** for production use.

**Key Takeaway**: The problem isn't the progressive approach itself, but rather:
1. How we prompt the model (too conversational)
2. What we ask it to do (discover vs generate)
3. How we validate output (too superficial)

The code is well-structured and can be salvaged with better prompts and validation. However, **this will require significant refinement** before being production-ready.

## Files Generated

Test outputs are backed up in:
- `/tmp/bad_outputs/README_32b.md` - README with 32b model
- `/tmp/bad_outputs/API_32b.md` - API with 32b model
- `/tmp/bad_outputs/CONTRIBUTING_32b.md` - CONTRIBUTING with 32b model
- `/tmp/bad_outputs/HRISA_32b.md` - HRISA with 32b model

Current (72b) outputs are in project root as README.md, API.md, CONTRIBUTING.md, HRISA.md.

## Next Steps

1. ✅ Restore original documentation from backups
2. ✅ Update config.yaml with model requirements
3. ✅ Commit progressive orchestrator code with "experimental" notice
4. ✅ Document findings in this file
5. ⏳ Plan v2 with refined prompts (future work)
