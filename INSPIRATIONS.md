# Inspirations & Framework Patterns

Reference materials and architectural patterns that informed the AI backtesting system design.

## Core Evaluation Frameworks

### 1. Promptfoo
**Best starting point for pattern matching**

- YAML-based test definitions
- GitHub Actions integration for PR-based testing
- Compares "before vs after" prompt changes automatically
- Supports regression testing with assertions
- `promptfoo/promptfoo-action@v1` posts results directly to PRs
- Can use previous outputs as baseline for comparison

**Key Pattern:** Treat prompt/configuration changes like code changes with automated diff testing

**Relevance:** Direct inspiration for YAML test format, assertion types, and PR comparison workflow

---

### 2. DSPy (Stanford NLP)
**Systematic prompt optimization**

- Treats prompts as compiled programs rather than strings
- MIPROv2 optimizer automatically tunes prompts based on metrics
- Uses training/validation sets to measure improvement
- Separates "what the system should do" from "how to prompt it"
- Can automatically generate and test prompt variations

**Key Pattern:** Automatic metric-driven optimization with clear train/test splits

**Relevance:** Inspired assertion registry pattern, optimization loops, and metric-driven evaluation

---

### 3. Evidently + GitHub Actions
**LLM regression testing in CI/CD**

- Released GitHub Action specifically for LLM regression testing
- Downloads test prompts, runs system, evaluates outputs
- Supports LLM judges and custom metrics
- Stores test datasets in cloud for collaboration
- Fails CI if quality metrics drop

**Key Pattern:** Treat AI system changes like code deployments with automated quality gates

**Relevance:** CI/CD integration pattern, GitHub Actions workflow template

---

### 4. CML (Continuous Machine Learning)
**ML-specific CI/CD**

- Integrates with GitHub Actions for ML workflows
- Generates performance reports as PR comments
- Includes visualizations (confusion matrices, metrics graphs)
- Treats model/prompt changes like code deployments

**Key Pattern:** Visual reporting and statistical significance in PR context

**Relevance:** Report generation approach, PR comment formatting

---

## Evaluation Metrics & Methodologies

### Code Quality Metrics (from ML evaluation literature)

**Pass@k (from HumanEval)**
- Probability that at least one of k samples passes tests
- Gold standard for code generation evaluation
- Simple, well-understood, reproducible
- **Recommendation:** Start with this metric

**CodeBLEU**
- BLEU adapted for code with Abstract Syntax Tree awareness
- Better for semantic similarity than character-level metrics
- Accounts for structure, not just surface similarity

**ChrF (Character n-gram F-score)**
- Shown to correlate better with human judgment than BLEU
- Less sensitive to minor variations
- Better for evaluation flexibility

**Code Quality Analysis**
- Cyclomatic complexity metrics
- Lint errors (pylint, ruff scores)
- Static analysis violations
- Execution performance metrics
- Test coverage metrics

**Comparison Metrics**
- Relative improvement/degradation percentages
- Statistical significance testing (critical!)
- Small improvements (<2 points) often aren't statistically significant

---

## Historical PR Mining Patterns

### RepoBench Approach
- Mines real code completion scenarios from GitHub history
- Uses real development context
- Pattern: Historical ground truth as validation

**Application:** Extract PR descriptions → expected code changes as test cases

### SWE-bench Pattern
- Uses real GitHub issues and their fixes as test cases
- Evaluates if AI reproduces actual developer solutions
- Realistic, complex scenarios
- Pattern: Real-world problem sets

**Application:** Historical successful PRs as "golden" test cases; measure if config changes maintain solution quality

### Your Innovation: PR History as Test Strategy
**Key insight:** Using historical PRs as backtesting data is like using historical trades in finance
- Extract problem (PR description/context) → solution (PR diff)
- Test new configurations against proven solutions
- Measure: "Does new config still produce acceptable fixes for this real scenario?"

---

## MCP-Specific Testing Patterns

### MCP Security Testing (from Promptfoo)
- Tests MCP servers with malicious/edge-case inputs
- Evaluates agent behavior with potentially problematic tool outputs
- Chain-of-thought validation

**Pattern:** Test full execution chain, not just the prompt

### Agent Framework Testing
- Build test harnesses that simulate full agent interactions
- Test tool selection accuracy
- Measure cascading effects of configuration changes
- Context window optimization tests

**Pattern:** Test in realistic execution context, not isolation

---

## Finance Backtesting Analogy

**Why this analogy works perfectly:**

| Finance | Code Generation |
|---------|-----------------|
| Strategy | Configuration (MCP, AGENTS.md, prompts) |
| Historical trades | Historical PRs |
| Performance metrics | Code quality metrics (Pass@k, CodeBLEU) |
| Walk-forward testing | PR replay testing |
| Drawdown | Quality degradation |
| Sharpe ratio | Code quality improvement ratio |
| Curve fitting risk | Overfitting to specific PR types |

**Key benefits of this frame:**
- Borrows rigorous statistical methodology
- Built-in concepts like significance testing, risk quantification
- Natural progression: backtest → forward test → live
- Familiar framework for engineers who trade/invest

---

## Similar/Competitive Tools to Study

### DeepEval
- Pytest-like testing framework for LLMs
- Pattern: Assertion-based evaluation
- Reference for assertion design

### LangSmith (LangChain's platform)
- Tracing and evaluation
- Dataset management
- Run comparison
- Reference for dataset handling

### Weights & Biases (wandb)
- ML/LLM evaluation features
- Visualization and comparison
- Reference for metrics visualization

### MLflow
- Model evaluation and comparison
- Artifact storage
- Experiment tracking
- Reference for artifact management

### Giskard
- Open-source ML testing framework
- Robustness testing patterns
- Reference for edge-case testing

---

## Key Architectural Patterns to Borrow

### 1. Pytest Plugin Pattern
- Discover test files by convention
- Dynamic test node creation
- Native CI/CD integration
- Standard output formats

### 2. Configuration as Code
- YAML for test definitions (Promptfoo style)
- Human-readable, version-controllable
- Easy to understand without code

### 3. Lazy Evaluation
- Cache expensive operations (LLM calls)
- Deterministic hashing for reproducibility
- Cost optimization built-in

### 4. Pluggable Validators
- Registry pattern for custom validators
- Composition over inheritance
- Easy to extend without modifying core

### 5. Progressive Reporting
- Simple text reports for CLI
- HTML reports for sharing
- Markdown for GitHub integration
- Structured output (JSON) for automation

---

## Implementation Priority Guidance

**From studying these frameworks:**

### Start Simple
1. Pass@k metric (simple, proven)
2. Deterministic assertions (regex, string matching)
3. Basic regression detection

### Add Gradually
4. LLM-as-judge for qualitative metrics
5. Code quality metrics (CodeBLEU, complexity)
6. Statistical significance testing

### Optimize Last
7. Automatic prompt/config tuning (DSPy-style)
8. Advanced visualization
9. Cost optimization through caching

---

## Citation/Attribution

This system synthesizes patterns from:
- **Promptfoo** (YAML tests, GitHub Actions integration)
- **DSPy** (Optimizer patterns, assertion framework)
- **Evidently** (LLM evaluation in CI/CD)
- **HumanEval/CodeBLEU** (Metrics)
- **Finance/Backtesting literature** (Methodology and statistical rigor)
- **SWE-bench/RepoBench** (Historical PR mining)
- **Pytest** (Test discovery and plugin system)

The key innovation: Combining all these patterns specifically for MCP/Agent configuration validation through historical PR backtesting.

---

## Further Reading

### Papers & References
- HumanEval: https://github.com/openai/human-eval
- CodeBLEU: https://arxiv.org/abs/2009.10297
- SWE-bench: https://github.com/princeton-nlp/swe-bench
- RepoBench: https://arxiv.org/abs/2403.03989

### Frameworks
- Promptfoo: https://github.com/promptfoo/promptfoo
- DSPy: https://github.com/stanfordnlp/dspy
- DeepEval: https://github.com/confident-ai/deepeval
- Giskard: https://github.com/Giskard-AI/giskard
