# GIT Guidelines
This document describes rules to follow when contributing to this codebase to collaborate cleanly, ensure consistency, and to enforce good coding practices

## GIT Branching + Pull Request Strategy
This section outlines our approach to branching, committing, and submitting pull requests for this project.

We follow a feature branching workflow, where the main branch is not directly updated. A new feature branch will be created for each feature/requirement. This will then be merged with other branches if necessary before being merged into the main branch.

### Branch Naming Convention
**task<*taskID*> taskname**

taskID and taskname correspond to Azure DevOps tasks

e.g. task16 setup documentation folder and guide
  
### Commit Message Convention 
**task<*taskID*> commit title (<*type*>)**

taskID corresponds to Azure DevOps tasks.
types: feature, bug fix, documentation, refactor, tests.
e.g. task16 update readMe file (documentation)

### Pull Request Naming Convention
**task<*taskID*> taskname**

taskID and taskname correspond to Azure DevOps tasks

e.g. task16 setup documentation folder and guide
- readMe file was updated
- documentation folder created with GIT guidelines and setup guide

### Pull Request Process
1. Create a pull request following the above naming convention
2. Include a description of key features achieved and screenshots if relevant
3. Share the link to the PR in the Discord server channel ‘pull-requests’ and ping members to request a review.
4. Each PR must be reviewed by another team member who may provide feedback or request changes.
5. Changes requested must be resolved and approved by the team member before any changes can be merged to the main branch.

## Other GIT policies
