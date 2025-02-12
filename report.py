# report.py
import time
from collections import Counter
from collections import defaultdict

import gspread
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa
from selenium.webdriver.support.ui import WebDriverWait
from requests import ReadTimeout

from google_form_package import Sheet
from process_handler import ProcessHandler

web_sheet = Sheet()
driver = web_sheet.set_driver()

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

def set_sheet2():
    worksheet = web_sheet.get_worksheet("Sheet2")
    worksheet.clear()
    worksheet.append_row(["number of jobs", "number of pages", "number of email notifications", "number of ads"])
    return worksheet

def set_report_sheet():
    worksheet = web_sheet.get_worksheet("ReportData")
    worksheet.clear()
    headers = ["number_of_jobs","number_of_email_notifications","number_of_ads"]
    worksheet.append_row(headers)
    return worksheet

def save_report_data(worksheet, report):
    for number_of_jobs, number_of_email_notifications, number_of_ads in report:
        worksheet.append_row([number_of_jobs, number_of_email_notifications, number_of_ads])

def load_report_data(worksheet) -> list[list[int]]:
    report = []
    rows = worksheet.get_all_values()
    for row in rows[1:]:
        if row and len(row) >= 3:
            try:
                number_of_jobs = int(row[0].strip())
                number_of_email_notifications = int(row[1].strip())
                number_of_ads = int(row[2].strip())
                report.append([number_of_jobs, number_of_email_notifications, number_of_ads])
            except ValueError:
                continue
    return report

def main():
    process_sheet = web_sheet.get_worksheet("Progress")
    ph = ProcessHandler(process_sheet, {"Processing": False, "UrlNum": 1}, "A3", shutdown_callback=lambda: save_report_data(report_sheet, report))
    progress = ph.load_progress()
    if not progress["Processing"]:
        set_sheet2()
        set_report_sheet()
    sheet2 = web_sheet.get_worksheet("Sheet2")
    report_sheet = web_sheet.get_worksheet("ReportData")
    report = load_report_data(report_sheet)
    progress["Processing"] = True
    while progress["Processing"]:
        try:
            url = f"https://au.jora.com/j?a=24h&l=Victoria&nofollow=true&p={progress['UrlNum']}&q=&r=0&sp=facet_distance&surl=0&tk=DE7LtoGm3BJx78CQKKAl-x1Ir1keUvqhw6PY4ybZ7"
            driver.get(url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"Current page: {url}")
            
            try:
                driver.find_element(By.CSS_SELECTOR, "a[class='next-page-button']")
            except NoSuchElementException:
                print("Finished scrapping")
                break

            print(f"current page: {url}")
            progress["UrlNum"] += 1

            jobs = driver.find_elements(By.CSS_SELECTOR, "a[class='job-link -no-underline -desktop-only show-job-description']")

            number_of_jobs = len(jobs)
            try:
                enot = driver.find_elements(By.CSS_SELECTOR, "form[class='email-alert-nudge-card-form']")
                number_of_email_notifications = len(enot)
            except NoSuchElementException:
                number_of_email_notifications = 0

            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                number_of_ads = 0
                for i in range(len(iframes)):
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    try:
                        iframe = iframes[i]
                    except IndexError:
                        continue
                    try:
                        driver.switch_to.frame(iframe)
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        try:
                            ads = WebDriverWait(driver, 20).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class*='clicktrackedAd_js']")))
                            number_of_ads += len(ads)
                        except TimeoutException:
                            pass
                    except Exception as e:
                        print(f"error during switching to iframe: {e}")
                    finally:
                        driver.switch_to.default_content()
            except NoSuchElementException:
                number_of_ads = 0
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
        append_row_with_retry(sheet2, row)

    driver.quit()
    save_report_data(report_sheet, report)
    progress["Processing"] = False
    progress["UrlNum"] = 1
    ph.save_progress(progress)
    process_sheet.update("A1", [[json.dumps({"progress":"setting", "UrlNum":1})]])
    process_sheet.update("A2", [[json.dumps({"finished": False, "RowNum": 1})]])
    print("Saved every data into the Google Sheet successfully.")

if __name__ == "__main__":
    main()
