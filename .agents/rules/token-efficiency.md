# Rule: Autonomous Agent Token Efficiency

## Guidelines for AI Coding Agents

1. **Targeted File Reads & Searches**:
   - Use ripgrep/grep searches rather than listing large directories or reading massive files end-to-end.
   - When inspecting model checkpoints or binary directories, avoid viewing non-text or binary files.
2. **Concise Tool Use**:
   - Limit outputs from shell commands using pipes (`head -n 20`, `grep`, etc.) or specific command flags.
3. **No Polling**:
   - When long-running tasks are sent to the background, avoid looping or polling status repeatedly; wait for system notifications.
4. **Structured Diffs**:
   - When modifying files, prefer precise surgical edits (`replace_file_content` or `multi_replace_file_content`) over whole-file replacements unless replacing small files.
