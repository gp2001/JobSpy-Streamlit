import streamlit as st
import pandas as pd
import csv
import uuid
from jobspy import scrape_jobs
from analytics import log_event, get_events_df, get_summary_stats

st.set_page_config(page_title="ICT Job Scraper 🚀", page_icon="🔎", layout="wide")

# ── App-level password gate ────────────────────────────────────────────────────
# Two access levels:
#   APP_PASSWORD         → standard access (Resume Matcher hidden)
#   RESUME_PASSWORD      → full access (Resume Matcher visible)
if not st.session_state.get("app_authenticated", False):
    st.title("🔐 ICT Group JobSpy")
    st.markdown("Please enter the access password to continue.")
    with st.form("app_login_form"):
        app_pwd = st.text_input("Password", type="password")
        login_submit = st.form_submit_button("Enter")
    if login_submit:
        try:
            pwd_standard = st.secrets["APP_PASSWORD"]
        except (KeyError, FileNotFoundError):
            pwd_standard = "ictgroupm&s"
        try:
            pwd_full = st.secrets["RESUME_PASSWORD"]
        except (KeyError, FileNotFoundError):
            pwd_full = "Pn0TpIF.[g#ND;#y"

        if app_pwd == pwd_full:
            st.session_state["app_authenticated"] = True
            st.session_state["resume_enabled"] = True
            st.rerun()
        elif app_pwd == pwd_standard:
            st.session_state["app_authenticated"] = True
            st.session_state["resume_enabled"] = False
            st.rerun()
        else:
            st.error("❌ Incorrect password. Please try again.")
    st.stop()
# ── End password gate ──────────────────────────────────────────────────────────

# ── Session identity & page-view tracking ─────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "session_logged" not in st.session_state:
    st.session_state["session_logged"] = True
    log_event(st.session_state["session_id"], "page_view")

_SID = st.session_state["session_id"]

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
_resume_enabled = st.session_state.get("resume_enabled", False)
_tab_labels = ["Company Info 📊", "Company Map 🗺️", "LinkedIn Profile Search 🕵️‍♂️"]
if _resume_enabled:
    _tab_labels.append("Resume Matcher 🤖")
_tab_labels.append("Admin 🔐")
tabs = st.tabs(_tab_labels)

# Tab index helpers
_ti_resume = _tab_labels.index("Resume Matcher 🤖") if _resume_enabled else None
_ti_admin  = _tab_labels.index("Admin 🔐")

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
                log_event(
                    _SID,
                    "job_search",
                    search_term=search_term,
                    location=location,
                    sites=", ".join(site_name),
                    results_count=len(jobs),
                )
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
        # Keep job title and URL alongside company/location for rich popups
        url_col = 'job_url' if 'job_url' in map_df.columns else ('url' if 'url' in map_df.columns else None)
        title_col = 'title' if 'title' in map_df.columns else None
        keep_cols = ['company', 'location', 'lat', 'lon']
        if title_col:
            keep_cols.append(title_col)
        if url_col:
            keep_cols.append(url_col)
        map_df = map_df[keep_cols].copy()
        map_df['company']  = map_df['company'].astype(str)
        map_df['location'] = map_df['location'].astype(str)
        map_df['lat']      = map_df['lat'].astype(float)
        map_df['lon']      = map_df['lon'].astype(float)
        st.write(f"Locations with coordinates: {len(map_df)}")
        if not map_df.empty:
            # Count vacancies per company
            company_vacancy_count = map_df.groupby('company').size().to_dict()

            # Aggregate lat/lon/location per company (first occurrence)
            company_data = map_df.groupby('company').agg({
                'lat': 'first',
                'lon': 'first',
                'location': 'first'
            }).reset_index()
            company_data['vacancy_count'] = company_data['company'].map(company_vacancy_count)

            # Build per-company job list for popups
            company_jobs = {}
            for _, job_row in map_df.iterrows():
                co = job_row['company']
                title   = str(job_row.get(title_col, '')) if title_col else ''
                job_url = str(job_row.get(url_col,   '')) if url_col   else ''
                company_jobs.setdefault(co, []).append((title, job_url))

            # Create Folium map centered on Netherlands
            netherlands_lat, netherlands_lon = 52.1326, 5.2913
            m = folium.Map(location=[netherlands_lat, netherlands_lon], zoom_start=7)

            max_vacancies = company_data['vacancy_count'].max()
            min_vacancies = company_data['vacancy_count'].min()

            for _, row in company_data.iterrows():
                company_name  = row['company']
                vacancy_count = row['vacancy_count']
                lat, lon      = row['lat'], row['lon']

                # Scale circle radius 10–40 by vacancy count
                radius = 10 + (vacancy_count - min_vacancies) / max(max_vacancies - min_vacancies, 1) * 30

                # Build job-links HTML
                jobs_html = ""
                for (job_title, job_url) in company_jobs.get(company_name, []):
                    label = job_title if job_title and job_title != 'nan' else "View job"
                    if job_url and job_url != 'nan':
                        jobs_html += f'<li><a href="{job_url}" target="_blank">{label}</a></li>'
                    else:
                        jobs_html += f'<li>{label}</li>'

                popup_html = f"""
                <div style="font-family:Arial; width:280px; max-height:300px; overflow-y:auto;">
                    <b style="font-size:15px; color:#FF6B6B;">🏢 {company_name}</b><br>
                    <hr style="margin:4px 0;">
                    <b>📍 Locatie:</b> {row['location']}<br>
                    <b>💼 Vacatures:</b> {vacancy_count}<br>
                    <hr style="margin:4px 0;">
                    <b>🔗 Openstaande vacatures:</b>
                    <ul style="margin:4px 0; padding-left:16px;">
                        {jobs_html}
                    </ul>
                </div>
                """

                # CircleMarker — visual size indicator
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=radius,
                    color='#FF6B6B',
                    fill=True,
                    fillColor='#FF6B6B',
                    fillOpacity=0.35,
                    weight=2,
                ).add_to(m)

                # Standard pin Marker — clickable, opens popup with job links
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=320),
                    tooltip=f"📌 {company_name} — {vacancy_count} vacature{'s' if vacancy_count != 1 else ''}",
                    icon=folium.Icon(color='red', icon='briefcase', prefix='fa'),
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
        log_event(_SID, "profile_search", search_term=query, results_count=len(df))
    else:
        st.info("Enter role, company, and click Search to find LinkedIn profiles.")

# ─────────────────────────────────────────────────────────────────────────────
# Tab 4 – Resume Matcher (only rendered when resume_enabled = True)
# ─────────────────────────────────────────────────────────────────────────────
if _resume_enabled:
    with tabs[_ti_resume]:
        st.title("Resume Matcher 🤖")
        st.markdown(
            "Upload your resume and let the AI find the best matching vacancies, "
            "then score and explain each match."
        )

        # ── Step 1: Upload ────────────────────────────────────────────────────────
        uploaded_resume = st.file_uploader(
            "📄 Upload your resume", type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT"
        )

        if uploaded_resume is not None:
            file_bytes = uploaded_resume.read()

            with st.spinner("Extracting text from resume…"):
                try:
                    from resume_matcher import extract_resume_text
                    resume_text = extract_resume_text(file_bytes, uploaded_resume.name)
                except Exception as exc:
                    st.error(f"Could not read the file: {exc}")
                    resume_text = ""

            if resume_text:
                with st.expander("📝 Extracted resume text (click to review / edit)"):
                    resume_text = st.text_area(
                        "Resume text", value=resume_text, height=300,
                        label_visibility="collapsed"
                    )

                # ── Step 2: Analyse resume with LLM ──────────────────────────────
                st.subheader("Step 1 – Analyse resume with AI")
                analyse_btn = st.button("🔍 Analyse Resume", key="analyse_resume_btn")

                if analyse_btn or st.session_state.get("resume_analysis"):
                    if analyse_btn:
                        with st.spinner("Connecting to Azure OpenAI and analysing resume…"):
                            try:
                                from resume_matcher import analyze_resume
                                analysis = analyze_resume(resume_text)
                                st.session_state["resume_analysis"] = analysis
                                st.session_state["resume_text"]     = resume_text
                            except Exception as exc:
                                st.error(f"LLM error: {exc}")
                                analysis = None
                    else:
                        analysis = st.session_state.get("resume_analysis")
                        resume_text = st.session_state.get("resume_text", resume_text)

                    if analysis:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**🎓 Experience level:** {analysis.get('experience_level','—').title()}")
                            st.markdown(f"**📋 Summary:** {analysis.get('summary','—')}")
                            st.markdown("**💼 Suggested job titles:**")
                            for t in analysis.get("job_titles", []):
                                st.markdown(f"  - {t}")
                        with col_b:
                            st.markdown("**🛠️ Key skills detected:**")
                            for s in analysis.get("skills", []):
                                st.markdown(f"  - {s}")
                            st.markdown("**🔎 Suggested search terms:**")
                            for q in analysis.get("search_terms", []):
                                st.markdown(f"  - `{q}`")

                        # ── Step 3: Search for jobs ───────────────────────────────
                        st.subheader("Step 2 – Search for vacancies")

                        default_search = (
                            analysis.get("search_terms", [""])[:1][0]
                            if analysis.get("search_terms") else ""
                        )

                        with st.form("resume_job_search_form"):
                            rm_search_term = st.text_input(
                                "Search term", value=default_search,
                                help="Pre-filled from the AI analysis; feel free to edit."
                            )
                            rm_location      = st.text_input("Location", value="Netherlands")
                            rm_results       = st.number_input("Max results", 1, 200, 50)
                            rm_hours_old     = st.number_input("Max job age (hours)", 1, 2000, 1000)
                            rm_country       = st.text_input("Indeed country", value="netherlands")
                            rm_sites         = st.multiselect(
                                "Sites to scrape",
                                ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"],
                                default=["indeed", "linkedin"],
                            )
                            rm_max_score     = st.number_input(
                                "Max jobs to score with AI (most recent first)",
                                min_value=1, max_value=50, value=10,
                                help="Scoring every job calls the LLM once per job — keep this low for speed."
                            )
                            rm_submit = st.form_submit_button("🚀 Find & Score Vacancies")

                        if rm_submit:
                            if not rm_sites:
                                st.warning("Select at least one site.")
                            else:
                                all_rm_jobs = []
                                failed_rm   = []
                                rm_progress = st.progress(0, text="Scraping jobs…")
                                for i, site in enumerate(rm_sites):
                                    rm_progress.progress(i / len(rm_sites), text=f"Scraping {site}…")
                                    try:
                                        result = scrape_jobs(
                                            site_name=[site],
                                            search_term=rm_search_term,
                                            location=rm_location,
                                            results_wanted=rm_results,
                                            hours_old=rm_hours_old,
                                            country_indeed=rm_country,
                                        )
                                        if result is not None and not result.empty:
                                            all_rm_jobs.append(result)
                                            st.toast(f"✅ {site}: {len(result)} jobs", icon="✅")
                                    except Exception as e:
                                        failed_rm.append((site, str(e).splitlines()[0]))
                                        st.toast(f"❌ {site} failed", icon="❌")

                                rm_progress.progress(1.0, text="Scraping done!")

                                if failed_rm:
                                    with st.expander(f"⚠️ {len(failed_rm)} site(s) failed"):
                                        for site, err in failed_rm:
                                            st.error(f"**{site}**: {err}")

                                if all_rm_jobs:
                                    jobs_df = pd.concat(all_rm_jobs, ignore_index=True)
                                    st.success(f"Found **{len(jobs_df)}** jobs. Scoring the top **{rm_max_score}**…")

                                    jobs_to_score = jobs_df.head(rm_max_score).copy()
                                    scores, strengths_list, gaps_list, explanations = [], [], [], []

                                    score_progress = st.progress(0, text="Scoring vacancies with AI…")
                                    from resume_matcher import score_job

                                    for idx, (_, row) in enumerate(jobs_to_score.iterrows()):
                                        score_progress.progress(
                                            (idx + 1) / len(jobs_to_score),
                                            text=f"Scoring {idx+1}/{len(jobs_to_score)}: {row.get('title','?')}…"
                                        )
                                        try:
                                            match_result = score_job(
                                                resume_text=st.session_state.get("resume_text", resume_text),
                                                job_title=str(row.get("title", "")),
                                                job_description=str(row.get("description", "")),
                                                company=str(row.get("company", "")),
                                            )
                                        except Exception as exc:
                                            match_result = {
                                                "score": 0,
                                                "strengths": [],
                                                "gaps": [],
                                                "explanation": f"Error: {exc}",
                                            }
                                        scores.append(match_result["score"])
                                        strengths_list.append(", ".join(match_result.get("strengths", [])))
                                        gaps_list.append(", ".join(match_result.get("gaps", [])))
                                        explanations.append(match_result["explanation"])

                                    score_progress.progress(1.0, text="Scoring complete!")

                                    jobs_to_score["match_score"]  = scores
                                    jobs_to_score["strengths"]    = strengths_list
                                    jobs_to_score["gaps"]         = gaps_list
                                    jobs_to_score["explanation"]  = explanations

                                    jobs_to_score = jobs_to_score.sort_values(
                                        "match_score", ascending=False
                                    ).reset_index(drop=True)
                                    st.session_state["rm_scored_jobs"] = jobs_to_score

                        # ── Display scored results ────────────────────────────────
                        scored = st.session_state.get("rm_scored_jobs", pd.DataFrame())
                        if not scored.empty:
                            st.subheader("🏆 Vacancy Match Results")
                            for i, row in scored.iterrows():
                                score = row.get("match_score", 0)
                                color = "🟢" if score >= 70 else ("🟡" if score >= 40 else "🔴")
                                with st.expander(
                                    f"{color} **{score}/100** — {row.get('title','?')} @ {row.get('company','?')} "
                                    f"({row.get('location','?')})"
                                ):
                                    st.markdown(f"**📊 Match score:** {score}/100")
                                    st.markdown(f"**💬 Explanation:** {row.get('explanation','—')}")
                                    if row.get("strengths"):
                                        st.markdown(f"**✅ Strengths:** {row.get('strengths','—')}")
                                    if row.get("gaps"):
                                        st.markdown(f"**⚠️ Gaps:** {row.get('gaps','—')}")
                                    job_url = row.get("job_url") or row.get("url", "")
                                    if job_url and str(job_url) != "nan":
                                        st.markdown(f"🔗 [View Job Posting]({job_url})")
                                    desc = str(row.get("description", ""))
                                    if desc and desc != "nan":
                                        st.markdown("**📄 Job Description:**")
                                        st.markdown(desc[:1500] + ("…" if len(desc) > 1500 else ""))

                            dl_cols = [
                                c for c in [
                                    "title", "company", "location", "match_score",
                                    "explanation", "strengths", "gaps", "job_url",
                                ] if c in scored.columns
                            ]
                            st.download_button(
                                "⬇️ Download scored results (CSV)",
                                scored[dl_cols].to_csv(index=False),
                                file_name="resume_matches.csv",
                                mime="text/csv",
                            )
            else:
                st.warning("Could not extract any text from the uploaded file. Please try a different file.")
        else:
            st.info("👆 Upload a resume (PDF, DOCX, or TXT) to get started.")


# ─────────────────────────────────────────────────────────────────────────────
# Tab 5 – Admin Dashboard
# ─────────────────────────────────────────────────────────────────────────────
with tabs[_ti_admin]:
    st.title("Admin Dashboard 🔐")

    # ── Login ────────────────────────────────────────────────────────────────
    if not st.session_state.get("admin_authenticated", False):
        st.markdown("This area is restricted to administrators.")
        with st.form("admin_login"):
            pwd = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")
        if login_btn:
            try:
                admin_pass = st.secrets["ADMIN_PASSWORD"]
            except (KeyError, FileNotFoundError):
                st.error(
                    "⚙️ **ADMIN_PASSWORD is not configured.** "
                    "Go to your Streamlit Cloud app → Settings → Secrets and add: "
                    "`ADMIN_PASSWORD = \"your-password\"`"
                )
                st.stop()
            if pwd == admin_pass:
                st.session_state["admin_authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    else:
        # ── Logout ───────────────────────────────────────────────────────────
        if st.button("Logout 🚪"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

        st.success("✅ Logged in as Admin")

        # ── KPI Metrics ──────────────────────────────────────────────────────
        stats = get_summary_stats()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("👁️ Page Views",       stats["page_views"])
        c2.metric("👤 Unique Sessions",   stats["unique_sessions"])
        c3.metric("📋 Total Events",      stats["total_events"])
        c4.metric("🔍 Job Searches",      stats["job_searches"])
        c5.metric("🕵️ Profile Searches",  stats["profile_searches"])

        events_df = get_events_df()

        if events_df.empty:
            st.info("No usage data recorded yet. Data appears here as users interact with the app.")
        else:
            events_df["timestamp"] = pd.to_datetime(events_df["timestamp"])
            events_df["date"] = events_df["timestamp"].dt.date

            # ── Activity over time ────────────────────────────────────────────
            st.subheader("📈 Activity Over Time")
            daily = (
                events_df.groupby(["date", "action"])
                .size()
                .reset_index(name="count")
                .pivot(index="date", columns="action", values="count")
                .fillna(0)
            )
            st.line_chart(daily)

            # ── Unique sessions per day ───────────────────────────────────────
            st.subheader("👥 Unique Users (Sessions) Per Day")
            daily_users = (
                events_df.groupby("date")["session_id"]
                .nunique()
                .reset_index(name="unique_sessions")
                .set_index("date")
            )
            st.bar_chart(daily_users)

            # ── Top search terms ──────────────────────────────────────────────
            search_events = events_df[
                (events_df["action"] == "job_search") & (events_df["search_term"] != "")
            ]
            if not search_events.empty:
                st.subheader("🔍 Top Job Search Terms")
                top_terms = (
                    search_events["search_term"]
                    .value_counts()
                    .head(10)
                    .rename_axis("search_term")
                    .reset_index(name="count")
                    .set_index("search_term")
                )
                st.bar_chart(top_terms)

            # ── Sites used ───────────────────────────────────────────────────
            if not search_events.empty and "sites" in search_events.columns:
                st.subheader("🌐 Sites Scraped (all-time)")
                sites_series = (
                    search_events["sites"]
                    .dropna()
                    .str.split(",")
                    .explode()
                    .str.strip()
                )
                sites_series = sites_series[sites_series != ""]
                if not sites_series.empty:
                    st.bar_chart(
                        sites_series.value_counts()
                        .rename_axis("site")
                        .reset_index(name="count")
                        .set_index("site")
                    )

            # ── Session table ────────────────────────────────────────────────
            st.subheader("🗒️ Sessions Summary")
            session_summary = (
                events_df.groupby("session_id")
                .agg(
                    first_seen=("timestamp", "min"),
                    last_seen=("timestamp", "max"),
                    total_events=("id", "count"),
                    job_searches=("action", lambda x: (x == "job_search").sum()),
                    profile_searches=("action", lambda x: (x == "profile_search").sum()),
                )
                .sort_values("last_seen", ascending=False)
                .reset_index()
            )
            st.dataframe(session_summary, use_container_width=True)

            # ── Raw event log ────────────────────────────────────────────────
            with st.expander("📋 Raw Event Log"):
                st.dataframe(
                    events_df.drop(columns=["id"]).reset_index(drop=True),
                    use_container_width=True,
                )
                st.download_button(
                    "⬇️ Download Event Log (CSV)",
                    events_df.to_csv(index=False),
                    file_name="analytics_events.csv",
                    mime="text/csv",
                )

