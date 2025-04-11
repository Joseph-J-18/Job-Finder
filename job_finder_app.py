import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os

st.set_page_config(page_title="Job Finder AI", layout="centered")
st.title("Job Finder & Auto-Apply AI")

# --- User Preferences ---
st.subheader("Your Job Preferences")
job_roles = ["Government", "Software Developer", "Data Analyst", "Associate Engineer", "Software Engineer"]
location = st.text_input("Preferred Location", value="Hyderabad")
experience = st.selectbox("Experience Level", ["Fresher", "Experienced"], index=0)
auto_apply = st.checkbox("Enable Auto-Apply", value=True)
resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

# --- SQLite Database to Track Applications ---
conn = sqlite3.connect("applications.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS applied_jobs (title TEXT, company TEXT, link TEXT, date_applied TEXT)")
conn.commit()

def track_application(job):
    c.execute("INSERT INTO applied_jobs VALUES (?, ?, ?, DATE('now'))", (job['Title'], job['Company'], job['Link']))
    conn.commit()

def has_applied(job):
    c.execute("SELECT * FROM applied_jobs WHERE link = ?", (job['Link'],))
    return c.fetchone() is not None

# --- Simple Job Scraper Function (demo with Naukri) ---
def get_naukri_jobs(role, location):
    query = role.replace(" ", "%20")
    url = f"https://www.naukri.com/{query}-jobs-in-{location.lower()}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    jobs = []
    for div in soup.find_all('article', class_='jobTuple')[:10]:
        title = div.find('a', class_='title')
        company = div.find('a', class_='subTitle')
        loc = div.find('li', class_='location')
        exp = div.find('li', class_='experience')
        link = title['href'] if title else ""
        jobs.append({
            'Title': title.text.strip() if title else "",
            'Company': company.text.strip() if company else "",
            'Location': loc.text.strip() if loc else "",
            'Experience': exp.text.strip() if exp else "",
            'Link': link
        })
    return jobs

# --- Selenium-Based Auto Apply (Demo Simulation) ---
def auto_apply_to_job(job):
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options)
        driver.get(job['Link'])
        time.sleep(2)
        driver.quit()
        track_application(job)
        return f"Auto-applied to {job['Title']} at {job['Company']}"
    except Exception as e:
        return f"Failed to auto-apply: {str(e)}"

# --- Job Search Button ---
if st.button("Find Jobs"):
    if not resume_file:
        st.warning("Please upload your resume to enable auto-apply.")
    else:
        all_jobs = []
        for role in job_roles:
            with st.spinner(f"Searching for {role} jobs in {location}..."):
                jobs = get_naukri_jobs(role, location)
                all_jobs.extend(jobs)
                time.sleep(1)

        if not all_jobs:
            st.warning("No jobs found. Try a different role or location.")
        else:
            st.success(f"Found {len(all_jobs)} jobs!")

            for job in all_jobs:
                if has_applied(job):
                    continue
                with st.expander(job['Title']):
                    st.write(f"**Company:** {job['Company']}")
                    st.write(f"**Location:** {job['Location']}")
                    st.write(f"**Experience Required:** {job['Experience']}")
                    st.markdown(f"[Apply Link]({job['Link']})")

                    if auto_apply:
                        result = auto_apply_to_job(job)
                        st.success(result)

# --- Application Tracker View ---
if st.checkbox("Show Applied Job History"):
    c.execute("SELECT * FROM applied_jobs")
    rows = c.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["Title", "Company", "Link", "Date Applied"])
        st.dataframe(df)
    else:
        st.info("No applications tracked yet.")
