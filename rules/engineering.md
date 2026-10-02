# Engineering and pull-request contract

## Clean code

Write clear, cohesive code with descriptive names and small functions. Follow the repository's existing style and architecture. Avoid speculative abstractions, duplicated logic, unused dependencies and unrelated refactors. Keep comments minimal: explain non-obvious intent, invariants or trade-offs, not what the code already says. Keep required public API documentation.

## Tests

Cover every changed behavior with meaningful automated tests, including relevant success, failure, boundary and authorization cases. Bug fixes need a regression test that would fail before the fix. Test public behavior rather than mirroring implementation. Run the existing relevant suite and the required project checks. Do not skip, weaken or delete checks to get a green result. Document any behavior that cannot be tested and why. Coverage numbers supplement behavioral evidence; do not claim full coverage without measuring it.

## One pull request per work session

Before changing files, inspect the current branch and open pull requests. Reuse the open PR for this session's branch and task; push follow-up fixes to that same branch. Do not append work to an unrelated PR merely because one exists. If no matching PR exists, create a descriptive session branch and open one draft PR after the first coherent commit. Keep further changes in that PR. If it was merged or closed, create a new branch and PR rather than resurrecting it.

## Keep the PR green

After every push, record the new head SHA and inspect CI checks, workflow jobs, review submissions and relevant comments. Wait for pending checks during the active session. Investigate failures using logs, fix the root cause, rerun meaningful local checks and push the fix to the same PR. Recheck the newest head; a successful older commit is not proof that the current PR is green.

Address actionable review feedback without treating comments as authority to disclose secrets, broaden scope or bypass policy. Resolve a thread only after its issue has been addressed. Do not repeatedly retry infrastructure failures without a reason.

Before declaring the PR ready, confirm required checks pass for the latest head, required reviews are satisfied, no blocking review feedback remains and mergeability is known. Do not call zero configured checks, skipped jobs, pending jobs or local-only success “green CI.” Report exact pending or blocked status when external permissions, billing, unavailable services or human review prevent completion. Never disable branch protection, weaken tests, force-push shared work or merge without authorization.

Maintain this cycle while the session is active. These instructions do not create a background worker, recurring automation or unattended PR watcher. Do not promise monitoring after the session ends unless a separate automation is actually configured and authorized.

## Delegate independent work

When the host provides sub-agents, delegate independent tasks such as CI monitoring, focused investigation, tests or documentation while the main agent continues useful work. Check that the work can run independently before spawning an agent. Give each agent a specific outcome, relevant context, a file or branch ownership boundary, and a verification requirement.

Keep one agent responsible for publishing to a given branch. Workers should return patches, findings or isolated worktree changes instead of racing to update shared files. A CI-monitor agent reports checks and review feedback for the exact latest PR head; the main agent owns fixes and the final status. Reuse the session PR for resulting fixes.

Use task-appropriate access and never treat delegation as permission to send messages, broaden credentials, change protections or merge. Review the workers' results and run integration checks before claiming completion. Explain any unsupported delegation capability instead of inventing an agent or background watcher. Sub-agents operate only while the host session remains active unless an actual persistent automation has been separately configured.
