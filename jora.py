from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
import time
import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict
from collections import Counter
import logging

user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(options=options)

def main():
    key = 'orbital-bank-448101-m4-45ac7ee07c01.json'
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    credentials = Credentials.from_service_account_file(key, scopes=scopes)
    gc = gspread.authorize(credentials)
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1iFZ71DNkAtlJL_HsHG6oT98zG4zhE6RrT2bbIBVitUA/edit?gid=0#gid=0"
    sh = gc.open_by_url(spreadsheet_url)

    sheet_name = "Sheet1"
    worksheet = sh.worksheet(sheet_name)
    worksheet.resize(rows=20000)
    worksheet.clear()
    worksheet.append_row(["job_code", "job_title", "company", "location", "salary", "job_type", "etc", "description"])

    sheet_3_name = "Sheet2"
    summary = sh.worksheet(sheet_3_name)
    summary.clear()
    summary.append_row(["number_of_jobs", "number_of_pages", "number_of_email_notifications", "number_of_ads"])

    seen_jobs = set()

    page_num = 1
    report = []
    while True:
        try:
            url = f"https://au.jora.com/j?a=24h&l=Victoria&nofollow=true&p={page_num}&q=&r=0&sp=facet_distance&surl=0&tk=DE7LtoGm3BJx78CQKKAl-x1Ir1keUvqhw6PY4ybZ7"
            driver.get(url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            next_button = driver.find_elements(By.CSS_SELECTOR, "a[class='next-page-button']")
            if not next_button:
                print("Finished scrapping")
                break

            print(f"current page: {url}")
            page_num += 1

            jobs = driver.find_elements(By.CSS_SELECTOR, "a[class='job-link -no-underline -desktop-only show-job-description']")

            number_of_jobs = len(jobs)
            for job in jobs:
                driver.execute_script("arguments[0].click();", job)
                time.sleep(1)

                try:
                    raw_job_title = driver.find_element(By.CSS_SELECTOR, "h3[class='job-title heading -size-xxlarge -weight-700']").text
                    job_link_data = driver.find_element(By.CSS_SELECTOR, "a[class = 'open-new-tab -link-cool']")
                    job_link = job_link_data.get_attribute("href")
                    job_title = f'=HYPERLINK("{job_link}", "{raw_job_title}")'
                except NoSuchElementException:
                    job_title = "No job title"

                try:
                    job_code = driver.find_element(By.CSS_SELECTOR,"button[class = 'save-job-button rounded-button -secondary -size-lg']").get_attribute("data-job-id")
                except NoSuchElementException:
                    job_code = "No job code"


                try:
                    company = driver.find_element(By.CSS_SELECTOR, "div.sticky-container span.company").text
                except NoSuchElementException:
                    company = "No company data"

                if (raw_job_title.strip().lower(), company.strip().lower()) in seen_jobs:
                    print(f"Duplicate found, skipping: {company}, {raw_job_title}")
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

                job_data = [job_code,
                            job_title,
                            company,
                            location,
                            salary,
                            job_type,
                            etc,
                            desc_string]
                worksheet.append_row(job_data, value_input_option="USER_ENTERED")
                seen_jobs.add((raw_job_title.lower(), company.lower()))
                time.sleep(1)

            try:
                enot = driver.find_elements(By.CSS_SELECTOR, "form[class='email-alert-nudge-card-form']")
                number_of_email_notifications = len(enot)
            except NoSuchElementException:
                number_of_email_notifications = 0

            number_of_ads = 0

            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    driver.switch_to.frame(iframe)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    try:
                        ads = WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class*='clicktrackedAd_js']")))
                        number_of_ads += len(ads)
                    except TimeoutException as e:
                        print(e)
                        pass
                    driver.switch_to.default_content()
            except NoSuchElementException as e:
                print(e)
                pass

            report_data = [number_of_jobs,
                               number_of_email_notifications,
                               number_of_ads]
            report.append(report_data)
        except NoSuchElementException as e:
            print(f"Error processing job: {e}")
            continue


        report_raw_data = defaultdict(list)
        for number_of_jobs, number_of_email_notifications, number_of_ads in report:
            report_raw_data[number_of_jobs].append((number_of_email_notifications, number_of_ads))

        summary_raw_data = []
        for number_of_jobs, entries in report_raw_data.items():
            num_pages = len(entries)
            num_email_notifications = Counter(entry[0] for entry in entries)
            number_of_ads = Counter(entry[1] for entry in entries)

            str_email_notifications = ", ".join(f"{key}:{value}" for key, value in num_email_notifications.items())
            str_ads = ", ".join(f"{key}:{value}" for key, value in number_of_ads.items())

            summary_raw_data.append([number_of_jobs, num_pages, str_email_notifications, str_ads])

    summary_raw_data.sort(key=lambda x: x[0])
    for row in summary_raw_data:
        summary.append_row(row, value_input_option="USER_ENTERED")

    driver.quit()
    print("Saved every data into the Google Sheet successfully.")

if __name__ == "__main__":
    main()