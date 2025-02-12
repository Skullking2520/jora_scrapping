# jora_detail.py
import re
import time

import gspread
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # noqa

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

def set_detail_sheet():
    worksheet = web_sheet.get_worksheet("DetailData")
    worksheet.clear()
    headers = ["company website","is from seek","is active"]
    worksheet.append_row(headers)
    return worksheet

def remove_hyperlink(cell_value):
    # remove hyper link
    if cell_value.startswith('=HYPERLINK('):
        pattern = r'=HYPERLINK\("([^"]+)"\s*,\s*"[^"]+"\)'
        match = re.match(pattern, cell_value)
        if match:
            return match.group(1)
    return cell_value

def extract():
    # extract from Sheet1
    sheet1 = web_sheet.get_worksheet("Sheet1")
    sheet1_header = sheet1.row_values(1)
    try:
        link_idx = sheet1_header.index("job link") + 1
    except ValueError as e:
        print("Could not detect requested row", e)
        return

    all_rows = sheet1.get_all_values()[1:]

    link_list = []

    for row_num, row in enumerate(all_rows, start=2):
        link = row[link_idx - 1] if len(row) >= link_idx else ""
        detail_url = remove_hyperlink(link)
        link_list.append({"link_row_num":row_num, "detail_url":detail_url})
    return link_list

def load_detail_data(worksheet) -> list[list[str]]:
    report = []
    rows = worksheet.get_all_values()
    for row in rows[1:]:
        if row and len(row) >= 3:
            try:
                company_website = row[0].strip()
                is_from_seek = row[1].strip()
                is_active = row[2].strip()
                report.append([company_website, is_from_seek, is_active])
            except ValueError:
                continue
    return report

def is_first_execution(progress_sheet):
    progress_value = progress_sheet.acell("A3").value
    return not progress_value or progress_value.strip() == ""

def main():
    process_sheet = web_sheet.get_worksheet("Progress")
    if is_first_execution(process_sheet):
        set_detail_sheet()
    sheet1 = web_sheet.get_worksheet("Sheet1")
    ph = ProcessHandler(process_sheet, {"finished": False, "RowNum": 1}, "A3")
    progress = ph.load_progress()
    extracted_list = extract()

    sheet1_header = sheet1.row_values(1)
    try:
        col_company_website = sheet1_header.index("company website") + 1
        col_is_active = sheet1_header.index("is active") + 1
        col_seek_link = sheet1_header.index("seek link") + 1
        col_is_from_seek = sheet1_header.index("is from seek") + 1
    except ValueError:
        print("Column not in sheet")
        return

    while not progress["finished"]:
        try:
            while progress["RowNum"] < len(extracted_list):
                row_and_index = extracted_list[progress["RowNum"]]
                row_num = row_and_index["link_row_num"]
                extracted_url = row_and_index["detail_url"]
                driver.get(extracted_url)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                try:
                    raw_is_from_seek = driver.find_element(By.CSS_SELECTOR,"span[class = 'site']").text
                    is_from_seek = bool("seek" in raw_is_from_seek)
                except NoSuchElementException:
                    is_from_seek = False

                try:
                    raw_company_website = driver.find_element(By.CSS_SELECTOR,"a[class = 'apply-button rounded-button -primary -size-lg -w-full']")
                    base_url = "https://au.jora.com"
                    raw_link = raw_company_website.get_attribute("href")
                    company_website = base_url + raw_link
                except NoSuchElementException:
                    company_website = "no company website"

                try:
                    raw_is_active = driver.find_element(By.CSS_SELECTOR,"div[class = 'flash-container error']").text
                    is_active = not bool("This job is no longer available" in raw_is_active)
                except NoSuchElementException:
                    is_active = True

                if is_from_seek:
                    seek_link = company_website
                    company_website = ""
                else:
                    seek_link = ""

                sheet1.update_cell(row_num, col_company_website, company_website)
                sheet1.update_cell(row_num, col_is_active, "Active" if is_active else "Inactive")
                sheet1.update_cell(row_num, col_seek_link, seek_link)
                sheet1.update_cell(row_num, col_is_from_seek, str(is_from_seek))

                progress["RowNum"] += 1
        except NoSuchElementException as e:
                print(f"Error processing job: {e}")
                continue

    driver.quit()
    progress["finished"] = True
    ph.save_progress(progress)
    print("Saved every data into the Google Sheet successfully.")

if __name__ == "__main__":
    main()
