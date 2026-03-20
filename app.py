import streamlit as st
import pandas as pd
import csv
from jobspy import scrape_jobs

st.set_page_config(page_title="ICT Job Scraper 🚀", page_icon="🔎", layout="wide")

st.sidebar.title("ICT Group JobSpy 🚀")
st.sidebar.markdown("""
**Welcome to ICT Group Job Scraper! 👋**

- 🌍 Scrape jobs from top platforms
- 🏢 Blocklist companies you don't want to see
- 🕵️‍♂️ Filter by company, download results, and more!

**Site status on Streamlit Cloud:**

| Site | Status |
|---|---|
| Indeed | ✅ Working |
| LinkedIn | ⚠️ Intermittent (rate-limited) |
| ZipRecruiter | ❌ 403 (EU GDPR) |
| Glassdoor | ❌ 400 (location parse) |
| Google | ❌ RetryError (rate-limit) |
| Bayt | ❌ 403 Forbidden |
| Naukri | ❌ 406 reCAPTCHA |
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
            default=["indeed", "linkedin"],
            help=(
                "✅ indeed — reliable on cloud\n"
                "⚠️ linkedin — intermittent (rate-limited on cloud IPs)\n"
                "❌ zip_recruiter — 403 GDPR geo-block (EU)\n"
                "❌ glassdoor — 400 / location not parsed on cloud IPs\n"
                "❌ google — RetryError (rate-limited on cloud IPs)\n"
                "❌ bayt — 403 Forbidden on cloud IPs\n"
                "❌ naukri — 406 reCAPTCHA required on cloud IPs"
            )
        )
        blocklist = st.text_area("Blocklist Companies (comma separated)", value="")
        submitted = st.form_submit_button("Scrape Jobs 🚀")

    if submitted:
        if not site_name:
            st.warning("Please select at least one site to scrape.")
        else:
            all_jobs = []
            failed_sites = []

            progress_bar = st.progress(0, text="Starting scrape...")
            for i, site in enumerate(site_name):
                progress_bar.progress((i) / len(site_name), text=f"Scraping {site}...")
                try:
                    result = scrape_jobs(
                        site_name=[site],
                        search_term=search_term,
                        google_search_term=google_search_term,
                        location=location,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        country_indeed=country_indeed,
                    )
                    if result is not None and not result.empty:
                        all_jobs.append(result)
                        st.toast(f"✅ {site}: {len(result)} jobs", icon="✅")
                except Exception as e:
                    failed_sites.append((site, str(e).splitlines()[0]))
                    st.toast(f"❌ {site} failed", icon="❌")

            progress_bar.progress(1.0, text="Done!")

            if failed_sites:
                with st.expander(f"⚠️ {len(failed_sites)} site(s) failed — click to see details"):
                    for site, err in failed_sites:
                        st.error(f"**{site}**: {err}")

            if all_jobs:
                jobs = pd.concat(all_jobs, ignore_index=True)
                st.success(f"🎉 Found {len(jobs)} jobs across {len(all_jobs)} site(s)!")
                jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
                st.session_state['df'] = jobs
                st.session_state['blocklist'] = blocklist
            else:
                st.error("No jobs found — all selected sites failed. Check the expander above for details.")

    # --- Results (persists across tab switches via session_state) ---
    df = st.session_state.get('df', pd.DataFrame())
    saved_blocklist = st.session_state.get('blocklist', '')

    if not df.empty:
        blocklist_companies = [c.strip().lower() for c in saved_blocklist.split(",") if c.strip()]
        display_df = df.copy()
        if blocklist_companies:
            display_df = display_df[~display_df['company'].str.lower().isin(blocklist_companies)]
        st.write(f"Showing {len(display_df)} jobs after blocklist filter.")
        companies = display_df['company'].unique()
        selected_companies = st.multiselect("Filter by Company 🏢", companies, default=list(companies))
        filtered_df = display_df[display_df['company'].isin(selected_companies)]
        st.dataframe(filtered_df)
        st.download_button("⬇️ Download CSV", filtered_df.to_csv(index=False), file_name="filtered_jobs.csv", mime="text/csv")
    elif submitted:
        st.warning("No jobs found. Try different search terms or locations! 😕")

with tabs[1]:
    st.title("Company Map 🗺️")
    st.info("After scraping jobs, companies with location data will be shown on the map below.")
    df = st.session_state.get('df', pd.DataFrame())
    if not df.empty and 'location' in df.columns:
        import folium
        from streamlit_folium import st_folium
        from geopy.geocoders import Nominatim
        import time

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
            # Count vacancies per company
            company_vacancy_count = map_df.groupby('company').size().to_dict()

            # Aggregate data by company and location (take first location per company)
            company_data = map_df.groupby('company').agg({
                'lat': 'first',
                'lon': 'first',
                'location': 'first'
            }).reset_index()
            company_data['vacancy_count'] = company_data['company'].map(company_vacancy_count)

            # Create Folium map centered on Netherlands
            netherlands_lat, netherlands_lon = 52.1326, 5.2913
            m = folium.Map(location=[netherlands_lat, netherlands_lon], zoom_start=7)

            # Normalize radius for circle markers (scale by vacancy count)
            max_vacancies = company_data['vacancy_count'].max()
            min_vacancies = company_data['vacancy_count'].min()

            # Add circle markers for each company with vacancy counts
            for _, row in company_data.iterrows():
                vacancy_count = row['vacancy_count']
                # Scale radius from 10 to 40 based on vacancy count
                radius = 10 + (vacancy_count - min_vacancies) / max(max_vacancies - min_vacancies, 1) * 30

                # Create popup with company and vacancy information
                popup_text = f"""
                <div style="font-family: Arial; width: 250px;">
                    <b style="font-size: 16px; color: #FF6B6B;">🏢 {row['company']}</b><br>
                    <hr style="margin: 5px 0;">
                    <b>Openstaande Vacatures:</b> {vacancy_count}<br>
                    <b>Locatie:</b> {row['location']}
                </div>
                """

                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=radius,
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{row['company']} - {vacancy_count} vacatures",
                    color='#FF6B6B',
                    fill=True,
                    fillColor='#FF6B6B',
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)

            st_folium(m, width=1000, height=600)

            # Show summary table with companies and vacancy counts
            st.subheader("📊 Vacatures per Bedrijf")
            summary_df = company_data[['company', 'vacancy_count', 'location']].sort_values('vacancy_count', ascending=False)
            summary_df.columns = ['Bedrijf', 'Aantal Vacatures', 'Locatie']
            st.dataframe(summary_df, use_container_width=True)
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
