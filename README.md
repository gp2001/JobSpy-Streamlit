# 🚀 JobSpy Streamlit App

A powerful job scraping web application built with Streamlit that aggregates job listings from multiple platforms including Indeed, LinkedIn, ZipRecruiter, Glassdoor, Google, Bayt, and Naukri.

## ✨ Features

### 📊 Job Scraping
- **Multi-platform support**: Scrape from 7+ job boards simultaneously
- **Advanced filtering**: Blocklist companies, filter by location and job title
- **Flexible parameters**: Control job age, result count, and search terms
- **CSV export**: Download results for offline analysis

### 🗺️ Geographic Visualization
- **Interactive map**: Visualize job locations with Pydeck
- **Location insights**: See where opportunities are concentrated
- **Cached geocoding**: Fast location lookups with caching

### 🕵️‍♂️ LinkedIn Profile Search
- **Bing-powered search**: Find LinkedIn profiles by role and company
- **Robust error handling**: Graceful fallback when Bing blocks access
- **Local optimization**: Full features available in local deployment

## 🚀 Quick Start

### Deploy to Streamlit Cloud

1. **Fork this repository** on GitHub
2. **Go to [Streamlit Cloud](https://share.streamlit.io)**
3. **Create new app**:
   - Repository: `JobSpy-Streamlit`
   - Branch: `main`
   - Main file: `app.py`
4. **Deploy!** 🎉

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

## 📋 Requirements

- Python 3.8+
- Streamlit >= 1.28.0
- pandas >= 1.3.0
- jobspy >= 0.2.3
- geopy >= 2.3.0
- pydeck >= 0.8.0
- selenium >= 4.11.0

## 📁 Project Structure

```
JobSpy-Streamlit/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .streamlit/
│   ├── config.toml            # Streamlit configuration
│   └── secrets.toml.example   # Example secrets file
├── modules/
│   ├── __init__.py
│   ├── scraper.py             # Job scraping utilities
│   └── search_profiles.py      # LinkedIn profile search
└── README.md
```

## 🎯 Usage

### Basic Job Scraping

1. Enter search parameters:
   - **Search Term**: Job title (e.g., "Data Scientist")
   - **Location**: Job location (e.g., "Netherlands")
   - **Sites**: Select job boards to scrape from
   - **Results**: How many results to return (25-50 recommended for cloud)

2. Click "Scrape Jobs 🚀"

3. View results and download as CSV

### Performance Tips

- ⚡ Start with 25-50 results for faster scraping
- 📍 Use specific locations for better results
- 🎯 Select 2-3 sites instead of all 7
- ⏱️ Expect 2-5 minutes for 50 results on Streamlit Cloud

### Known Limitations

- **LinkedIn Profile Search**: Limited in cloud environment, works best locally
- **Timeout**: Scraping >100 results may timeout on Streamlit Cloud
- **Rate limits**: Some sites may rate-limit rapid requests

## ⚙️ Configuration

### Environment Variables (Optional)

For Streamlit Cloud, add secrets via app settings:
1. App Settings → Advanced Settings → Secrets
2. Add any required API keys or configuration

Example `.streamlit/secrets.toml`:
```toml
[api_keys]
your_api_key = "value"
```

## 🔧 Troubleshooting

### "Module not found" Error
- Install all dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version`

### Timeout Errors
- Reduce `results_wanted` to 25-50
- Limit sites to 2-3
- Increase timeout in `streamlit_requirements.txt` if needed

### LinkedIn Search Not Working
- Expected on Streamlit Cloud (browser automation limitations)
- Run locally for full LinkedIn search functionality
- Use `streamlit run app.py` with `headless=False`

### Map Not Displaying
- Ensure jobs have location data
- Check for geocoding errors in logs
- Verify Pydeck is installed: `pip install pydeck`

## 📚 Documentation

- [Streamlit Docs](https://docs.streamlit.io)
- [JobSpy Library](https://github.com/Bunsly/JobSpy)
- [Pydeck Documentation](https://pydeck.gl)

## 🛠️ Development

### Local Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/JobSpy-Streamlit.git
cd JobSpy-Streamlit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Adding New Features

1. Create a new module in `modules/`
2. Import in `app.py`
3. Add UI components using Streamlit
4. Test locally before deploying

## 📝 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

For issues or questions:
- Check the [Troubleshooting](#-troubleshooting) section
- Review [GitHub Issues](https://github.com/yourusername/JobSpy-Streamlit/issues)
- Check Streamlit Cloud logs

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Job scraping powered by [JobSpy](https://github.com/Bunsly/JobSpy)
- Maps powered by [Pydeck](https://pydeck.gl)

---

**Happy job hunting! 🎯**

Made with ❤️ for the job search community

