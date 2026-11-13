---
name: process-documentor
description: Use this skill when using antigravity to build something substantial that requires an implementation plan. It ensures that the plan is broken down into smaller tasks, each with its own description and estimated time to complete.
---

# Process Documentor Skill

This skill ensures that transient files such as implementation plan, walkthroughs, work logs, task descriptions etc. are saved to the filesystem and can be reviewed by the user when needed at a later time. Save the implementation plan to a file called Plan_{TIMESTAMP}.md in the root of the project. Save changes to the implementation plan back in the same markdown document. Similarly save walkthroughs in a file called Walkthrough_{TIMESTAMP}.md, task descriptions in a file called Task_{TIMESTAMP}.md, and work logs in a file called Worklog_{TIMESTAMP}.md. Update and reuse existing plan/walkthrough/worklog/task files as needed, but make sure that you create a new file when creating a new implementation plan.

# Commit changes regularly

Each time substantial changes are made to source files, prompt the user to commit the changes to the local repository. The prompt should be in the form of a question: "Do you want to commit the changes made to the source files?". If the user agrees, commit the changes to the local repository, and include a short summary of relevant changes in the commit message. If the user does not agree, do not commit the changes.

# Do not commit the generated process files.

The implementation plan, walkthrough, task description, and work log files are for the user's reference only. Do not commit them to the local repository. 