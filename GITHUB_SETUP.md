# 🚀 GitHub Repository Setup Instructions

Your local JobSpy-Streamlit repository is ready! Follow these steps to push it to GitHub:

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click the **"+"** icon in the top right
3. Select **"New repository"**
4. Fill in the details:
   - **Repository name**: `JobSpy-Streamlit`
   - **Description**: "A powerful job scraping web app built with Streamlit"
   - **Public** or **Private** (recommended: Public for community contributions)
   - **Do NOT initialize** with README, .gitignore, or license (we have them)
   - Click **"Create repository"**

## Step 2: Add Remote and Push

Copy and run these commands in PowerShell from the JobSpy-Streamlit directory:

```powershell
cd "C:\Users\Gabriel.Shamon\Documents\GitHub\JobSpy-Streamlit"

# Add the remote repository (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/JobSpy-Streamlit.git

# Verify the remote was added
git remote -v

# Create and switch to main branch (if not already)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 3: Verify Push

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/JobSpy-Streamlit`
2. Check that all files are there:
   - ✅ app.py
   - ✅ requirements.txt
   - ✅ search_profiles.py
   - ✅ .streamlit/config.toml
   - ✅ README.md
   - ✅ CONTRIBUTING.md
   - ✅ .gitignore

## Step 4: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub account
4. Choose repository: `JobSpy-Streamlit`
5. Set main file: `app.py`
6. Click "Deploy" 🎉

Your app will be live in 1-2 minutes!

## Step 5 (Optional): Add GitHub Topics

To help others discover your project:

1. Go to your repository settings
2. Scroll to "About" section
3. Add topics: `streamlit`, `job-scraper`, `web-app`, `python`

## Step 6 (Optional): Enable GitHub Pages

To add a website:

1. Go to Settings → Pages
2. Select `main` branch as source
3. Your repo README will be published

---

## Troubleshooting

### "repository not found" error
- Check that you replaced `YOUR_USERNAME` with your actual GitHub username
- Verify the repository exists on GitHub
- Check that you're authenticated: `git config --list`

### "Authentication failed" error
- Use personal access token instead of password
- Go to GitHub → Settings → Developer settings → Personal access tokens
- Create a new token with `repo` scope
- Use token as password when prompted

### Files not showing on GitHub
- Verify all files were added: `git status`
- Check commit was created: `git log`
- Ensure you're on main branch: `git branch`
- Try pushing again: `git push origin main`

---

## Repository Structure

```
JobSpy-Streamlit/
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml         # Example secrets
├── app.py                   # Main Streamlit application
├── search_profiles.py       # LinkedIn profile search module
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
├── CONTRIBUTING.md         # Contribution guidelines
└── .gitignore             # Git ignore rules
```

## Next Steps

After pushing:

1. ✅ Test the Streamlit Cloud deployment
2. ✅ Share the deployed app URL: `https://share.streamlit.io/YOUR_USERNAME/JobSpy-Streamlit/app.py`
3. ✅ Add a link to your GitHub repository in your profile/portfolio
4. ✅ Consider adding GitHub Actions for CI/CD
5. ✅ Encourage community contributions

---

**Questions?** Check the [GitHub Help](https://docs.github.com/en/github/getting-started-with-github) or see the CONTRIBUTING.md file in the repository.

**Ready to deploy?** 🚀 Follow Step 1-4 above!

