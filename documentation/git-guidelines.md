# GIT Guidelines
This document describes rules to follow when contributing to this codebase to collaborate cleanly, ensure consistency, and to enforce good coding practices

## GIT Branching + Pull Request Strategy
This section outlines our approach to branching, committing, and submitting pull requests for this project.

We follow a feature branching workflow, where we do not work off the main branch and will create a new branch for a each feature/requirement. This will then be merged with other branches if necessary before being merged into the main branch.

### Branch Naming Convention
task<taskID> taskname
taskID and taskname correspond to Azure DevOps tasks
e.g. task16 setup documentation folder and guide
  
### Commit message convention 
task<taskID> commit title(<type>)
taskID corresponds to Azure DevOps tasks.
types: feature, bug fix, documentation, refactor, tests.
e.g. task16 update readMe file (documentation)

### Pull Request Naming Convention
task<taskID> taskname
taskID corresponds to Azure DevOps tasks.

Include a description of key features achieved and screenshots if relevant.
Each PR will have to be approved by one member that is chosen by the member who initiated the PR after they have read through, provided any feedback if necessary, and make any changes if necessary.

e.g. task16 setup documentation folder and guide
- readMe file was updated
- documentation folder created with GIT guidelines and setup guide

## Other GIT policies
