# PowerShell Commands - Copy & Paste Ready

## Setup Commands

This file contains ready-to-copy PowerShell commands for pushing to GitHub.

### Command 1: Navigate to Repository
```powershell
cd "C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit"
```

### Command 2: Configure Git (Optional - only if not already done)
```powershell
git config user.name "Gabriel Shamon"
git config user.email "gabriel.shamon@example.com"
```

### Command 3: Add Remote Repository
**⚠️ IMPORTANT: Replace `YOUR_USERNAME` with your GitHub username first!**

For example, if your GitHub username is `gshamon`, use:
```powershell
git remote add origin https://github.com/gshamon/JobSpy-Streamlit.git
```

Generic template:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/JobSpy-Streamlit.git
```

### Command 4: Set Main Branch
```powershell
git branch -M main
```

### Command 5: Push to GitHub
```powershell
git push -u origin main
```

When prompted for password, use your **personal access token** (not your GitHub password).

---

## Complete Push Sequence

Copy and run these all at once:

```powershell
cd "C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit"
git remote add origin https://github.com/YOUR_USERNAME/JobSpy-Streamlit.git
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME` before running!**

---

## Verification Commands

After pushing, verify everything worked:

```powershell
# Check remote was added
git remote -v

# Check current branch
git branch

# Check recent commits
git log --oneline -5

# View repository status
git status
```

---

## If You Make Mistakes

### Remove wrong remote
```powershell
git remote remove origin
```

### Try adding remote again
```powershell
git remote add origin https://github.com/YOUR_USERNAME/JobSpy-Streamlit.git
```

### Force push (use with caution!)
```powershell
git push -u origin main --force
```

---

## Getting Your Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click: "Generate new token"
3. Name: `JobSpy-Push`
4. Check: `repo` (all checkboxes under repo)
5. Click: "Generate token"
6. **Copy the token immediately** (you won't see it again)
7. Use this token as password when git asks

---

## Environment Variables (Permanent Authentication)

To avoid entering token every time:

### Windows PowerShell (Permanent)
```powershell
# Run this once to store credentials
git config --global credential.helper wincred

# Or use personal access token in URL
git remote add origin https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/JobSpy-Streamlit.git
```

---

## Example Workflow

Here's how it should look when you run it:

```powershell
PS C:\Users\Gabriel.Shamon\Documents\GitHub> cd JobSpy-Streamlit

PS C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit> git remote add origin https://github.com/gshamon/JobSpy-Streamlit.git

PS C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit> git branch -M main

PS C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit> git push -u origin main
Enumerating objects: 15, done.
Counting objects: 100% (15/15), done.
Delta compression using up to 8 threads
Compressing objects: 100% (13/13), done.
Writing objects: 100% (15/15), 2.45 KiB | 490.00 B/s, done.
Total 15 (delta 0), reused 0 (delta 0), received 0
To https://github.com/gshamon/JobSpy-Streamlit.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.

PS C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit>
```

If you see this output, **your push was successful!** 🎉

---

## Next: Streamlit Cloud Deployment

After GitHub push succeeds:

1. Go to: https://share.streamlit.io
2. Click: "New app"
3. Select your repository: `YOUR_USERNAME/JobSpy-Streamlit`
4. Set main file: `app.py`
5. Click: "Deploy"

Your app will be live at:
```
https://share.streamlit.io/YOUR_USERNAME/JobSpy-Streamlit/app.py
```

---

## Common Commands Reference

```powershell
# Check all remotes configured
git remote -v

# See current branch
git branch

# Check uncommitted changes
git status

# View commit history
git log --oneline

# Add files (already done)
git add -A

# Make a commit (already done)
git commit -m "Your message"

# Push to main branch
git push origin main

# Pull latest from GitHub
git pull origin main
```

---

**Ready? Follow the "Complete Push Sequence" above with YOUR_USERNAME replaced!** 🚀

