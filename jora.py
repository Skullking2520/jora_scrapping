# jora.py
import datetime
import os
import re
import time
import locale
import gspread
import openai
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from requests import ReadTimeout

from google_form_package import Sheet
from process_handler import ProcessHandler

from zoneinfo import ZoneInfo

locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
malaysia_tz = ZoneInfo("Asia/Kuala_Lumpur")

web_sheet = Sheet()
driver = web_sheet.set_driver()

    # function for use of generative AI to differentiate job category using job title and description
# def open_ai(job:str, desc:str)->str:
#     # To use this in GitHub action, key secrecy is required

#     openai_api_key = os.environ.get("OPENAI_API_KEY", "")
#     openai.api_key = openai_api_key

#     if not openai_api_key:
#         return "No API Key"

#     question = (f"The following details are a part of a job posting."
#                 f"1) job title: {job}"
#                 f"2) description: {desc}"
#                 f""
#                 f"You are required to give out the category of the job in one keyword depending on the provided information."
#                 f"If description is empty, find the category based on job title. If both are empty, give no answer."
#                 f"No additional explanation is needed. Just give the Job Category."
#                 f"example: 'Hospitality', 'IT', 'Customer Service', 'Healthcare', 'Retail', 'Construction' etc")
#     response = openai.chat.completions.create(model="gpt-3.5-turbo",
#                                             messages=[
#                                                 {"role": "system", "content": "You are a helpful assistant for job categorization."},
#                                                 {"role": "user", "content": question}],temperature=0.0,max_tokens=30)
#     job_category = response.choices[0].message.content.strip()
#     return job_category


def append_row_with_retry(worksheet, data, retries=3, delay=5):
    for attempt in range(retries):
        try:
            worksheet.append_row(data, value_input_option="USER_ENTERED")
            return
        except gspread.exceptions.APIError as e:
            if any(code in str(e) for code in ["500", "502", "503", "504","429"]) or isinstance(e, ReadTimeout):
                print(f"Error occurred. Retry after {delay} seconds ({attempt+1}/{retries})")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"Failed to append element {data} after {retries} attempts.")
                return

def set_sheet1():
    worksheet = web_sheet.get_worksheet("Sheet1")
    worksheet.clear()
    worksheet.append_row(["job code", "job title", "job link", "company", "location", "salary", "job type", "etc", "company website", "is from seek", "seek link", "scrap date", "job listing date", "is active", "job category", "description"])
    return worksheet

def set_seen_jobs_data_sheet():
    worksheet = web_sheet.get_worksheet("JobData")
    worksheet.clear()
    headers = ["job title", "company"]
    worksheet.append_row(headers)
    return worksheet

def load_to_seen_data():
    sheet1 = web_sheet.get_worksheet("Sheet1")
    sheet1_data = sheet1.get_all_values()
    prepopulated_rows = []
    for row in sheet1_data[1:]:
        if len(row) >= 4:
            job_title = row[1].strip()
            company = row[3].strip()
            if job_title and company:
                prepopulated_rows.append([job_title, company])
    job_data_sheet = web_sheet.get_worksheet("JobData")
    if prepopulated_rows:
        job_data_sheet.append_rows(prepopulated_rows, value_input_option="USER_ENTERED")

def save_seen_jobs_data(worksheet, seen_jobs):
    rows = [[job_title, company] for job_title, company in seen_jobs]
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

def load_seen_jobs_data(worksheet) -> set[tuple[str, str]]:
    seen_jobs = set()
    rows = worksheet.get_all_values()
    for row in rows[1:]:
        if row and len(row) >= 2:
            job_title = row[0].strip().lower()
            company = row[1].strip().lower()
            seen_jobs.add((job_title, company))
    return seen_jobs

# main function where scrapping and Google Docs addition is done
def main():
    process_sheet = web_sheet.get_worksheet("Progress")
    sheet1 = web_sheet.get_worksheet("Sheet1")
    seen_sheet = web_sheet.get_worksheet("JobData")
    sheet1.resize(cols=17)
    load_to_seen_data()
    seen_jobs = load_seen_jobs_data(seen_sheet)
    ph = ProcessHandler(process_sheet, {"progress":"setting", "UrlNum":1}, "A1", shutdown_callback=lambda: save_seen_jobs_data(seen_sheet, seen_jobs))
    progress = ph.load_progress()
    if not sheet1.acell("A2").value:
        set_sheet1()
        set_seen_jobs_data_sheet()
    sheet1.update([["Running Scrapping"]], "Q1")
    
    while not progress["progress"] == "finished":
        try:
            progress["progress"] = "progressing"
            url = f"https://au.jora.com/j?a=24h&l=Victoria&nofollow=true&p={progress['UrlNum']}&q=&r=0&sp=facet_distance&surl=0&tk=DE7LtoGm3BJx78CQKKAl-x1Ir1keUvqhw6PY4ybZ7"
            driver.get(url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            try:
                driver.find_element(By.CSS_SELECTOR, "a[class='next-page-button']")
            except NoSuchElementException:
                progress["progress"] = "finished"
                ph.save_progress(progress)
                print("Finished scrapping")
                break

            print(f"current page: {url}")
            progress["UrlNum"] += 1

            jobs = driver.find_elements(By.CSS_SELECTOR, "a[class='job-link -no-underline -desktop-only show-job-description']")

            for job in jobs:
                driver.execute_script("arguments[0].click();", job)
                time.sleep(1)

                try:
                    job_title = driver.find_element(By.CSS_SELECTOR,"h3[class='job-title heading -size-xxlarge -weight-700']").text
                    job_link_data = driver.find_element(By.CSS_SELECTOR, "a[class = 'open-new-tab -link-cool']")
                    job_link = job_link_data.get_attribute("href")
                except NoSuchElementException:
                    job_title = "No job title"
                    job_link = "No job link"

                try:
                    job_code = driver.find_element(By.CSS_SELECTOR,"button[class = 'save-job-button rounded-button -secondary -size-lg']").get_attribute("data-job-id")
                except NoSuchElementException:
                    job_code = "No job code"

                try:
                    company = driver.find_element(By.CSS_SELECTOR, "div.sticky-container span.company").text
                except NoSuchElementException:
                    company = "No company data"

                if (job_title.strip().lower(), company.strip().lower()) in seen_jobs:
                    print(f"Duplicate found, skipping: {company}, {job_title}")
                    continue

                try:
                    badges = driver.find_elements(By.CSS_SELECTOR, "div.sticky-container div.badge.-default-badge")
                    tags_list = []
                    salary = "No salary given"
                    job_type = "No job_type given"
                    etc = "No etc given"
                    for badge in badges:
                        tags_list.append(badge.text)
                    for tag in tags_list:
                        if "$" in tag:
                            salary = tag
                        elif tag == "Casual/Temporary" or "time" in tag:
                            job_type = tag
                        else:
                            etc = tag
                except NoSuchElementException:
                    salary = "No salary given"
                    job_type = "No job_type given"
                    etc = "No etc given"


                try:
                    location = driver.find_element(By.CSS_SELECTOR, "div.sticky-container span.location").text
                except NoSuchElementException:
                    location = "No location given"

                try:
                    raw_date_added_dif = driver.find_element(By.CSS_SELECTOR, "span[class='listed-date']").text
                    now = datetime.datetime.now(malaysia_tz)
                    match = re.search(r'(?i)(\d+)\s*(day|hour)s?', raw_date_added_dif)
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2).lower()
                        if unit == "day":
                            job_listing_date = now - datetime.timedelta(days=num)
                        elif unit == "hour":
                            job_listing_date = now - datetime.timedelta(hours=num)
                        else:
                            job_listing_date = "No date added given"
                    else:
                        job_listing_date = "No date added given"
                except NoSuchElementException:
                    job_listing_date = "No date added given"

                scrap_date = datetime.datetime.now(malaysia_tz).strftime("%Y-%m-%d %H:%M:%S")

                try:
                    description = driver.find_element(By.CSS_SELECTOR, "div[class='job-description-container']")
                    description_elements = description.find_elements(By.XPATH, "./*")
                    job_desc = {}
                    desc_title = ""
                    job_desc[desc_title] = []

                    for element in description_elements:
                        tag_name = element.tag_name.lower()
                        text = element.text.strip()

                        if not text:
                            continue

                        if tag_name == "strong":
                            desc_title = text
                            job_desc[desc_title] = []
                        else:
                            job_desc[desc_title].append(text)

                    desc_string = ""
                    for title, content in job_desc.items():
                        desc_string += f"{title}"
                        for item in content:
                            desc_string += f"\n - {item}"
                        desc_string += "\n"
                except NoSuchElementException:
                    desc_string = "No description given"

                if job_link != "No job link":
                    job_hyper_link = f'=HYPERLINK("{job_link}", "{job_link}")'
                else:
                    job_hyper_link = job_link
                    
                job_category = ""
                # job_category = open_ai(job=job_title, desc=desc_string)

                job_data = [job_code,
                            job_title,
                            job_hyper_link,
                            company,
                            location,
                            salary,
                            job_type,
                            etc,
                            "",
                            "",
                            "",
                            scrap_date,
                            str(job_listing_date),
                            "",
                            job_category,
                            desc_string]
                append_row_with_retry(sheet1, job_data)
                seen_jobs.add((job_title.lower(), company.lower()))
                time.sleep(1)
            
        except NoSuchElementException as e:
            print(f"Error processing job: {e}")
            continue

    set_seen_jobs_data_sheet()
    driver.quit()
    print("Saved every data into the Google Sheet successfully.")

if __name__ == "__main__":
    main()
