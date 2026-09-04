# Skills Catalog

This catalog documents each skill's trigger phrases, required inputs, outputs, and validation commands.

## Skill Definitions

### acquire-codebase-knowledge

**Trigger Phrases**:
- "map this codebase"
- "document this architecture"
- "onboard me to this repo"
- "create codebase docs"
- "explain this repository structure"
- "show me how to work with this codebase"

**Required Inputs**:
- None (uses repository structure and existing files)

**Outputs**:
- `docs/codebase/STACK.md` - Technology stack and dependencies
- `docs/codebase/STRUCTURE.md` - Directory organization and file layout
- `docs/codebase/ARCHITECTURE.md` - System architecture and component relationships
- `docs/codebase/CONVENTIONS.md` - Coding conventions and patterns
- `docs/codebase/INTEGRATIONS.md` - External dependencies and integration points
- `docs/codebase/TESTING.md` - Testing approach and test coverage
- `docs/codebase/CONCERNS.md` - Known concerns and mitigation strategies

**Validation Commands**:
```bash
# Verify all seven documents exist
ls docs/codebase/*.md

# Check for [TODO] and [ASK USER] markers
grep -r "\[TODO\]" docs/codebase/
grep -r "\[ASK USER\]" docs/codebase/

# Validate traceability
grep -r "evidence:" docs/codebase/
```

**Metadata**:
- Version: "1.3"
- Compatibility: Python 3.8+ and git
- Enhancements: Multi-language manifest detection, CI/CD pipeline detection, container/orchestration detection

---

### code-reviewer

**Trigger Phrases**:
- "review this PR"
- "review this change"
- "security review"
- "operational impact review"
- "check for regressions"
- "validate deployment changes"
- "audit security changes"

**Required Inputs**:
- Pull request or change context
- Repository context files (engineering principles, security rules, etc.)

**Outputs**:
- Findings ordered by severity
- File-level references with concrete remediation
- Residual risks and testing gaps
- Concise change summary

**Validation Commands**:
```bash
# Check for security risks
grep -r "security" .ai/instructions/security-rules.md

# Verify policy enforcement
grep -r "policy" .ai/context/*.md

# Validate resource constraints
grep -r "resource" .ai/instructions/kubernetes-rules.md
```

**Review Priorities**:
1. Functional correctness and behavioral regressions
2. Security risks and policy bypasses
3. Reliability and production safety defaults
4. Resource limits, cost controls, and operational readiness
5. Documentation and runbook completeness

---

### educational-comments

**Trigger Phrases**:
- "teach me about"
- "explain this concept"
- "show me how to"
- "walk through this example"
- "demo this pattern"
- "explain the best practices"

**Required Inputs**:
- User's learning request
- Target concept or pattern

**Outputs**:
- Educational content explaining the concept
- Code examples demonstrating the pattern
- Best practices and guidelines
- Common pitfalls and mitigation

**Validation Commands**:
```bash
# Check for educational content
grep -r "teach" .ai/skills/educational-comments/

# Verify examples exist
find .ai/skills/educational-comments/ -name "*.py" -o -name "*.yaml"
```

---

### review-and-refactor

**Trigger Phrases**:
- "refactor this code"
- "clean up this codebase"
- "remove unused imports"
- "fix code quality issues"
- "optimize this implementation"
- "modernize this code"

**Required Inputs**:
- Codebase context
- Specific files or patterns to refactor

**Outputs**:
- Refactored code with improvements
- Documentation of changes
- Validation of refactored code

**Validation Commands**:
```bash
# Check for unused imports
grep -r "import.*unused" .ai/skills/

# Verify refactored code quality
find . -name "*.py" -exec python -m py_compile {} \;
```

---

### senior-devops-architect

**Trigger Phrases**:
- "design this infrastructure"
- "architect this deployment"
- "plan this infrastructure"
- "design CI/CD pipeline"
- "design monitoring setup"
- "design security architecture"
- "design observability setup"

**Required Inputs**:
- Infrastructure requirements
- Technology stack preferences
- Security and operational constraints

**Outputs**:
- Infrastructure architecture design
- Component relationships and dependencies
- Deployment and operational procedures
- Security and monitoring design

**Validation Commands**:
```bash
# Check for infrastructure design
grep -r "architecture" .ai/skills/senior-devops-architect/

# Verify deployment procedures
find .ai/skills/senior-devops-architect/ -name "*.yaml" -o -name "*.yml"
```

---

### senior-mlops-architect

**Trigger Phrases**:
- "design ML pipeline"
- "design model training pipeline"
- "design model serving"
- "design model monitoring"
- "design model registry"
- "design data versioning"
- "design experiment tracking"
- "design ML lifecycle"

**Required Inputs**:
- ML pipeline requirements
- Technology stack preferences
- Security and operational constraints

**Outputs**:
- ML pipeline architecture design
- Component relationships and dependencies
- Training, serving, monitoring patterns
- Model registry and data versioning design

**Validation Commands**:
```bash
# Check for ML pipeline design
grep -r "pipeline" .ai/skills/senior-mlops-architect/

# Verify training patterns
find .ai/skills/senior-mlops-architect/ -name "*.py" -o -name "*.yaml"
```

---

## Skill Usage Guidelines

### Trigger Detection

Skills are triggered when user prompts match the trigger phrases listed above. The assistant analyzes intent and selects the most appropriate skill.

### Input Requirements

Each skill has specific input requirements. Some skills require repository context files to be read first (e.g., engineering principles, security rules).

### Output Validation

After skill execution, validation commands help verify the skill's outputs are complete and correct.

### Metadata Tracking

Each skill definition includes metadata about version, compatibility, and enhancements. This helps track skill evolution and compatibility.

---

## Skill Integration

Skills are integrated into the repository intelligence system:

- **Context**: Skills are referenced in `.ai/context/` and `.ai/retrieval/` files
- **Instructions**: Skills follow rules in `.ai/instructions/` files
- **Retrieval**: Skills are part of the retrieval priority and routing system
- **Session**: Skills are recorded in `.ai/session/` for session tracking

---

## Skill Evolution

Skills are versioned and tracked for compatibility:

- Version numbers indicate major and minor releases
- Compatibility notes indicate required environments
- Enhancement lists track new capabilities

Regular skill catalog updates ensure accurate documentation of skill capabilities and usage patterns.
