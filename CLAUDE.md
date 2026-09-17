# Claude Agent Rules

Part A: Local rules

1. For nontrivial ad-hoc commands (more than 3 lines), ALWAYS write a bash script in `scripts/`. Also avoid long CLI commands like `sleep 5 && curl http://localhost | python -c...` . Write a temporary script instead, and edit it to do other ad-hoc commands.

2. Test things yourself rather than asking the user to test. Use browser automation (e.g. Playwright) for UI verification, unit tests for logic.

3. Code standards:
   - Functions under 50 lines, single responsibility
   - No duplicated logic — extract shared code

4. For new features: write one happy-path test per public function or endpoint. Skip tests that duplicate higher-level coverage or test trivial/unlikely-to-fail code paths.

5. Code comments: Document intent behind implementation in comments (business domain level), not low level detail that's easily seen from the code itself. Use super concise clear language. Only comment when nessecary

6. Git commits: Always ask the user before committing. Show them the diff or summary of changes and wait for approval.

Part B: Behavioral guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting. Mention it and ask for permission first.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.