## 1. Baseline And Isolation

- [x] 1.1 Confirm that the Git development baseline contains the unchanged active `chatgpt-web` files and that `python3 -m py_compile chatgpt-web/scripts/chatgpt_web.py` passes.
- [x] 1.2 Commit OpenSpec bootstrap and validated change artifacts on the baseline branch, without modifying the active `/Users/qingshan/.agents/skills/chatgpt-web` deployment.
- [x] 1.3 Create a GSD-managed isolated implementation worktree/milestone from the committed baseline and record its path for Codex review.

## 2. Return Protocol And Token Control

- [x] 2.1 In `chatgpt-web/scripts/chatgpt_web.py`, add `receipt`, `capsule`, and `full` return modes with `capsule` as the default for `ask` and `delegate`.
- [x] 2.2 Implement prompt augmentation and strict `<codex_capsule>` JSON parsing, output length limiting, and failure output that returns status plus URL without raw-answer fallback.
- [x] 2.3 Implement metadata-only metrics recording for response length, printed length, estimated avoided context, mode, status, and cleanup result; never store prompt text, answer text, credentials, or API keys.

## 3. Conversation Routing And Concurrency

- [x] 3.1 Preserve recent-topic continuation by default and explicit `--new` creation only; retain safe `list`, `discover`, and `select` flows.
- [x] 3.2 Add atomic single-task locking with clear failure output for concurrent attempts and no queue, hanging task, or persisted prompt body.
- [x] 3.3 Add tests proving invalid/redirected saved conversations stop before sending and never silently become new topics.

## 4. Nonintrusive Chrome Lifecycle

- [x] 4.1 Research and document the OpenCLI target/Chrome window identification behavior needed to identify an owned temporary automation window using a unique run marker.
- [x] 4.2 Implement macOS owned-window identification and minimize behavior before task prompt submission, using the normal authenticated Chrome/OpenCLI path and aborting safely if uniqueness cannot be proven.
- [x] 4.3 Implement cleanup that releases locks and closes only confirmed owned automation resources on success or failure, without quitting Chrome or altering user windows.

## 5. Skill Instructions And Automated Verification

- [x] 5.1 Update `chatgpt-web/SKILL.md` and `chatgpt-web/agents/openai.yaml` to describe low-token defaults, conversation rules, window lifecycle, and explicit full-return escape hatch.
- [x] 5.2 Add focused unit tests for capsule extraction/truncation, return-mode defaults, metrics redaction, lock behavior, and window-identification failure behavior using mocked subprocess/AppleScript calls.
- [x] 5.3 Run `python3 -m py_compile`, all new unit tests, and `python3 /Users/qingshan/.codex/skills/.system/skill-creator/scripts/quick_validate.py chatgpt-web`; provide actual command output to Codex.

## 6. Codex Review And Controlled Acceptance

- [x] 6.1 Codex reviews the implementation diff for scope, security, token-return boundaries, session routing, lock cleanup, and absence of key/cookie/body logging; request corrections for any defect.
- [x] 6.2 Codex runs `openspec validate chatgpt-web-low-token-bridge --strict --no-interactive` and repeats all automated tests independently in the isolated worktree.
- [x] 6.3 With user awareness before visible browser interaction, Codex executes a minimal real OpenCLI/ChatGPT no-send test to verify owned authenticated window minimization and cleanup; recent-topic and capsule routing remain covered by automated tests until a live message is authorized.
- [x] 6.4 Only after all acceptance checks pass, Codex deploys reviewed files to `/Users/qingshan/.codex/skills/chatgpt-web` and does not push the newly added `chatgpt-web` directory to GitHub without separate user authorization.
