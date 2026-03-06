import streamlit as st
import pandas as pd
import csv
from jobspy import scrape_jobs

st.set_page_config(page_title="ICT Job Scraper 🚀", page_icon="🔎", layout="wide")

st.sidebar.title("ICT Group JobSpy 🚀")
st.sidebar.markdown("""
**Welcome to ICT Group Job Scraper! 👋**

- 🌍 Scrape jobs from top platforms: Indeed, LinkedIn, ZipRecruiter, Glassdoor, Google, Bayt, Naukri
- 🏢 Blocklist companies you don't want to see
- 🕵️‍♂️ Filter by company, download results, and more!
""")

# --- Main Tabs ---
tabs = st.tabs(["Company Info 📊", "Company Map 🗺️", "LinkedIn Profile Search 🕵️‍♂️"])

with tabs[0]:
    st.title("Company Information 📊")
    with st.form("job_form"):
        st.subheader("🔍 Search for Jobs or Candidates")
        search_term = st.text_input("Search Term", value="Data scientist")
        google_search_term = st.text_input("Google Search Term", value="Data scientist nederland")
        location = st.text_input("Location", value="Almelo, Netherlands")
        results_wanted = st.number_input("Results Wanted", min_value=1, max_value=1000, value=200)
        hours_old = st.number_input("Max Job Age (hours)", min_value=1, max_value=2000, value=1000)
        country_indeed = st.text_input("Indeed Country", value="netherlands")
        site_name = st.multiselect(
            "Sites to Scrape",
            ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "bayt", "naukri"],
            default=["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "bayt", "naukri"]
        )
        blocklist = st.text_area("Blocklist Companies (comma separated)", value="")
        submitted = st.form_submit_button("Scrape Jobs 🚀")

    if submitted:
        with st.spinner("Scraping jobs, please wait... ⏳"):
            jobs = scrape_jobs(
                site_name=site_name,
                search_term=search_term,
                google_search_term=google_search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country_indeed,
            )
            st.success(f"🎉 Found {len(jobs)} jobs!")
            jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            df = pd.DataFrame(jobs)
            st.session_state['df'] = df  # Store df in session_state for use in other tabs
            if not df.empty:
                blocklist_companies = [c.strip().lower() for c in blocklist.split(",") if c.strip()]
                if blocklist_companies:
                    df = df[~df['company'].str.lower().isin(blocklist_companies)]
                st.write(f"Showing {len(df)} jobs after blocklist filter.")
                companies = df['company'].unique()
                selected_companies = st.multiselect("Filter by Company 🏢", companies, default=list(companies))
                filtered_df = df[df['company'].isin(selected_companies)]
                st.dataframe(filtered_df)
                st.download_button("⬇️ Download CSV", filtered_df.to_csv(index=False), file_name="filtered_jobs.csv", mime="text/csv")
            else:
                st.warning("No jobs found. Try different search terms or locations! 😕")

with tabs[1]:
    st.title("Company Map 🗺️")
    st.info("After scraping jobs, companies with location data will be shown on the map below.")
    df = st.session_state.get('df', pd.DataFrame())
    if not df.empty and 'location' in df.columns:
        import pydeck as pdk
        import geopy
        from geopy.geocoders import Nominatim
        import time
        from collections import defaultdict

        geolocator = Nominatim(user_agent="jobspy_map")

        # Only geocode unique, non-empty locations
        unique_locations = df['location'].dropna().unique()
        st.write(f"Unique locations to geocode: {len(unique_locations)}")

        # Use a cache to avoid repeated geocoding
        if 'geocode_cache' not in st.session_state:
            st.session_state['geocode_cache'] = {}
        geocode_cache = st.session_state['geocode_cache']

        latitudes = []
        longitudes = []
        progress = st.progress(0)
        for i, loc in enumerate(df['location']):
            if pd.isnull(loc) or not str(loc).strip():
                latitudes.append(None)
                longitudes.append(None)
                continue
            if loc in geocode_cache:
                lat, lon = geocode_cache[loc]
            else:
                try:
                    location_obj = geolocator.geocode(loc, timeout=10)
                    if location_obj:
                        lat, lon = location_obj.latitude, location_obj.longitude
                    else:
                        lat, lon = None, None
                except Exception:
                    lat, lon = None, None
                geocode_cache[loc] = (lat, lon)
                time.sleep(1)  # avoid hitting geocoding rate limits
            latitudes.append(lat)
            longitudes.append(lon)
            progress.progress((i+1)/len(df))
        df['lat'] = latitudes
        df['lon'] = longitudes
        st.session_state['df'] = df  # Update session_state with lat/lon
        map_df = df.dropna(subset=['lat', 'lon'])
        # Only keep serializable columns and ensure correct types
        map_df = map_df[['company', 'location', 'lat', 'lon']].copy()
        map_df['company'] = map_df['company'].astype(str)
        map_df['location'] = map_df['location'].astype(str)
        map_df['lat'] = map_df['lat'].astype(float)
        map_df['lon'] = map_df['lon'].astype(float)
        st.write(f"Locations with coordinates: {len(map_df)}")
        if not map_df.empty:
            # Use IconLayer for pins with tooltips
            icon_data = {
                "url": "https://cdn-icons-png.flaticon.com/512/684/684908.png",  # Pin icon
                "width": 128,
                "height": 128,
                "anchorY": 128
            }
            map_df["icon_data"] = [icon_data] * len(map_df)
            # Set initial focus to the Netherlands
            netherlands_lat, netherlands_lon = 52.1326, 5.2913
            st.pydeck_chart(pdk.Deck(
                map_style='mapbox://styles/mapbox/streets-v11',
                initial_view_state=pdk.ViewState(
                    latitude=netherlands_lat,
                    longitude=netherlands_lon,
                    zoom=7,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        "IconLayer",
                        data=map_df,
                        get_icon="icon_data",
                        get_position='[lon, lat]',
                        size_scale=20,  # Larger pins
                        pickable=True,
                    ),
                ],
                tooltip={
                    "html": "<b>Company:</b> {company}<br/><b>Location:</b> {location}",
                    "style": {"color": "white"}
                }
            ))
            st.write("Companies mapped:", map_df[['company', 'location', 'lat', 'lon']])
        else:
            st.warning("No mappable company locations found. Try scraping jobs with valid, specific location data (e.g., city names).")
    else:
        st.info("No job/company data available yet. Scrape jobs first.")

with tabs[2]:
    st.title("LinkedIn Profile Search 🕵️‍♂️")
    role = st.text_input("Role / Function", value="Data Scientist")
    company = st.text_input("Company", value="ICT Group")
    max_results = st.number_input("Max Results", min_value=1, max_value=50, value=5)
    search_btn = st.button("Search LinkedIn Profiles")

    if search_btn:
        query = f"{company} {role}"
        with st.spinner("Searching..."):
            from search_profiles import selenium_bing_linkedin_search
            df = selenium_bing_linkedin_search(query, max_results=int(max_results))
        st.success(f"Found {len(df)} LinkedIn profiles.")
        st.dataframe(df)
    else:
        st.info("Enter role, company, and click Search to find LinkedIn profiles.")
