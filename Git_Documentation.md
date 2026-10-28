# Git

- A version-control where it records project history, lets engineer works in parallel, can do code reviews and can investigate the mistakes
- it got 4 areas:
  - Working directory - files that exists on the current disk(`git add`)
  - Staging area - this where the changes will be selected for next commit(`git commit`)
  - Local repo - where we store commits and branches in our machine(`git push`) - tracked in .git/
  - Remote repo - a shared copy of our work(`git pull/git fetch`)

`git init(initializing the git in the folder) -> git add.(stage the files to the git) -> git commit -m "msg"(stage the files so that it can store in the history)-> git remote add origin <repo_url>(connects to the  remote repo so that history data can be saved in it) -> git push -u origin main(push the saved commits into remote repo through the brach where the files live)`

## Key Features

- Commit: - a snapshot of the project with a msg which points out to the parent
- branch: - a movable pointer to a commit
- HEAD: - points out where we are at!

### Setup & repos

- `git --version`
  - It helps to print the installed version
  - `winget install --id Git.Git -e` - helps to install the git

- `git config`
  - Helps to do changes to the git settings and every commit records an author
  - we use it for first setting up of git using our personal email
    - ``git config --global user.name "name"`` - to set the user name globally for once
    - ``git config --global user.email "email"`` - to set the user email globally for once
    - ``git config --list --show-origin`` - helps to see all the git settings
  - `--system` - specify to all users
  - `--global` - specify to the user
  - `--local` - can override the others

- `git init`
  - Turns the current folder into git
  - we usually use it whenever we start a new project locally

- `git clone`
  - helps to copy an existing remote repo with it's local history and sets up the origin
  - we use it when we pull anything which is open source
    - `git clone --depth 1 <repo_url>` - where it downloads only the latest snapshot, not the full history
    - `git clone --branch <branch> <repo_url>` - where it downloads the repo along with the specified branch
    - `git clone --recurse-submodules <repo_url>` - where it downloads the sub modules as well

### Inspecting State of the repo &  history

- `git status`
  - shows the changes what we have done in the folder

- `git diff`
  - it shows the changes in line-level
    - `git diff --staged` - helps to see the changes which are staged (what will go in the next commit)
    - `git diff --stat` - helps to show the summary
    - `git diff main...HEAD` - changes on our branch since we split it
- we use this before performing commit to check the status of the git

- `git log`
  - helps to list the git history
    - `git log --oneline` - shows one line per commit
    - `git log --oneline --graph --all` - shows the branches as a graph
    - `git log -n <number>` - shows the last n commits
    - `git log -- <file>` - shows the history of that particular file
  - we use it when we want to investigate the work

- `git show`
  - helps to show a single commit
  - `git show <commit-hash>`

- `git blame`
  - helps to show who changed each line of the file last and in which commit
  - use when we want to investigate what actually changed and why (the reason is in that commit's message)
  - `git blame <file>`

- `git grep`
  - helps to search the text from the tracked files
  - `git grep "text wanted to search"`

- `git shortlog`
  - helps to summarize the commits done by author
  - `git shortlog -sn`

### Staging & Committing

- `git add`
  - helps to move the file to the staging area
    - `git add .` - stage everything in the folder
    - `git add -A` - stage everything in the repo
    - `git add -p` - can stage interactively chunk by chunk
    - `git add -u` - can stage the already-tracked files

- `git commit`
  - helps to save the staged snaps to the history
    - `git commit -m "message"` - helps to save the already staged files with one-line
    - `git commit -am "message"` - helps to stages the changes and deletions in tracked files then commit
  
- `git commit --amend`
  - helps to re-write the most recent commit (message or content)
  - use it only before pushing, because it changes the commit

- `git rm`
  - helps to delete a file and stages the deletion
  - `git rm <file name that wants to be deleted>`
  - `git rm --cached <file>` - stops tracking the file but keeps it in our folder

- `git mv`
  - helps to rename a file and stages it
  - `git mv <old file> <new file>`

- `.gitignore`
  - a lightweight file listing of patterns where the git should not track
  - helps to keep the secrets out from the repo, but only if we add it before the first commit
  - if the file is already tracked we need `git rm --cached <file>` first

### Branching

- Branch: lets you work on fixes while isolating the main
- `git branch`
  - helps to list out the current branch, create,rename and delete the branches
    - `git branch -a` - work on local and remote branches
    - `git branch <name>` - helps to create the branches
    - `git branch -m <new_name>` - helps to rename the branch name
    - `git branch -d <name>` - helps to delete the branch (refuses if it's not merged)
    - `git branch -D <name>` - force deletes the branch
    - `git branch --merged` - list out the merged branches
    - `git push origin --delete <branch>` - helps to delete the remote branch

- `git switch`
  - helps to change the current branch
    - `git switch -c <new-branch>` - can create and switch to the created branch
    - `git switch -` - can jump back to previous branch

### Remotes & Collaboration

- `git remote`
  - helps to manage the connections that are connected to remote repos
    - `git remote -v` - list the remote repos along with their urls
    - `git remote add origin <url>` - helps to connect a local repo(made with git init) to a remote repo

- `git fetch`
  - helps to download new commits from the remote repo without changing our files or branches
  - so it's safe, we can check what changed before merging it
    - `git fetch <name>` - helps to fetch from the respective repo
    - `git fetch --all --prune` - fetch from all remotes and removes the branches deleted on remote

- `git pull`
  - helps to download new commits and merge them into the current branch (fetch + merge)
  - `git pull --rebase`- helps to fetch and replay our local commits on top of the new ones, so the history stays in a straight line
  - `git pull --ff-only`- helps to fetch and move the branch forward, and fails if the branches have diverged

- `git push`
  - helps to update our local commits to the remote
    - `git push <remote> <branch>` - push to the respective remote repo and to it's branch
    - `git push -u origin <branch>` - first push of a new branch, sets the upstream so next time only `git push` works
    - `git push --force-with-lease` - safer force push, stops if someone else pushed in between (never force push on main)
    - `git push origin --delete <branch>` - deletes the branch on the remote

### Integrating Changes

- `git merge`
  - helps to bring another branch's history into our current branch
  - we use it when a feature is done and needs to go into main
    - `git switch main` then `git merge <branch>` - merges the branch into main
    - `git merge --no-ff <branch>` - always makes a merge commit so the branch history is kept
    - `git merge --squash <branch>` - combines all the changes into one staged change, then we commit it
    - `git merge --abort` - cancels the merge which is in progress
  - fast-forward - if main has no new commits git just moves the pointer, no merge commit is made

- `git rebase`
  - helps to replay our commits on top of another branch, so the history becomes a straight line
  - we use it to update our feature branch with the latest main without extra merge commits
    - `git switch <feature-branch>` then `git rebase main` - puts our commits on top of latest main
    - `git rebase -i HEAD~n` - interactive, helps to reword, squash, drop or reorder the last n commits
    - `git rebase --continue` - after solving the conflicts
    - `git rebase --abort` - cancels the rebase
  - never rebase the commits which are already pushed and pulled by others, since it rewrites the history

- merge vs rebase
  - merge keeps the exact history and adds a merge commit, safe for shared branches
  - rebase rewrites the history into a line, use it only on our own branches

- `git revert`
  - helps to make a new commit which undoes an earlier commit
  - the history is not rewritten so it's the safe way to undo something which is already pushed
    - `git revert <commit-hash>` - undoes that commit
    - `git revert -m 1 <merge-commit-hash>` - undoes a merge commit

### Undoing and recovering

- `git restore`
  - helps to restore files from the pervious commits
    - `git restore <file name>` - helps to restore the file
    - `git restore --staged <file name>` - helps to restore the unstaged files
    - `git restore .` - helps to discard all the unstaged changes
