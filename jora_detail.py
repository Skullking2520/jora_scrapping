# jora_detail.py
import re
import time
import json

import gspread
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC  # noqa
from requests import ReadTimeout

from google_form_package import Sheet
from process_handler import ProcessHandler

web_sheet = Sheet()
driver = web_sheet.set_driver()

def append_row_with_retry(worksheet, data, retries=3, delay=65):
    for attempt in range(retries):
        try:
            worksheet.append_row(data, value_input_option="USER_ENTERED")
            return
        except gspread.exceptions.APIError as e:
            if any(code in str(e) for code in ["500", "502", "503", "504","429"]) or isinstance(e, ReadTimeout):
                print(f"Error occurred. Retry after {delay} seconds ({attempt+1}/{retries})")
                time.sleep(delay)
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
        if not detail_url:
            break
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

def batch_update_cells(worksheet, row_num, updates, retries=3, delay=5):
    sheet_id = getattr(worksheet, 'id', None) or worksheet._properties.get('sheetId')
    requests = []

    for col, value in updates:
        requests.append({
            "updateCells": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": row_num - 1,
                    "endRowIndex": row_num,
                    "startColumnIndex": col - 1,
                    "endColumnIndex": col
                },
                "rows": [{
                    "values": [{
                        "userEnteredValue": {"stringValue": str(value)}
                    }]
                }],
                "fields": "userEnteredValue"
            }
        })

    body = {"requests": requests}

    for attempt in range(1, retries + 1):
        try:
            worksheet.spreadsheet.batch_update(body)
            return
        except gspread.exceptions.APIError as e:
            if any(code in str(e) for code in ["500", "502", "503", "504", "429"]):
                print(f"[Retryable] Batch update error: {e}")
            else:
                print(f"[Non-retryable] Batch update error: {e}")
            print(f"Retrying after {delay} seconds (attempt {attempt}/{retries})")
            time.sleep(delay)
            delay *= 2
    raise Exception("Batch update failed after multiple retries")
    
def main():
    process_sheet = web_sheet.get_worksheet("Progress")
    sheet1 = web_sheet.get_worksheet("Sheet1")
    extracted_list = extract()
    ph = ProcessHandler(process_sheet, {"progress":"setting", "RowNum": 0}, "A2")
    progress = ph.load_progress()
    if progress["progress"] == "setting":
        set_detail_sheet()
    sheet1_header = sheet1.row_values(1)
    try:
        col_company_website = sheet1_header.index("company website") + 1
        col_is_active = sheet1_header.index("is active") + 1
        col_seek_link = sheet1_header.index("seek link") + 1
        col_is_from_seek = sheet1_header.index("is from seek") + 1
    except ValueError:
        print("Column not in sheet")
        return

    while not progress["progress"] == "finished":
        try:
            progress["progress"] = "processing"
            while progress["RowNum"] < len(extracted_list):
                row_and_index = extracted_list[progress["RowNum"]]
                row_num = row_and_index["link_row_num"]
                extracted_url = row_and_index["detail_url"]
                try:
                    driver.get(extracted_url)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                except:
                    progress["RowNum"] += 1
                    continue

                try:
                    raw_is_from_seek = WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span[class='site']"))
                    ).text
                    is_from_seek = "seek" in raw_is_from_seek.lower()
                except (NoSuchElementException, TimeoutException):
                    is_from_seek = False

                try:
                    raw_company_website = driver.find_element(By.CSS_SELECTOR,"a[class = 'apply-button rounded-button -primary -size-lg -w-full']")
                    company_website = raw_company_website.get_attribute("href")
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

                updates = [(col_company_website, company_website),(col_is_active, "Active" if is_active else "Inactive"),(col_seek_link, seek_link),(col_is_from_seek, str(is_from_seek))]
                batch_update_cells(sheet1, row_num, updates)

                progress["RowNum"] += 1
            progress["progress"] = "finished"
        except NoSuchElementException as e:
                print(f"Error processing job: {e}")
                continue
            
    process_sheet.update("A1", [[json.dumps({"progress":"setting", "UrlNum": 1})]])
    process_sheet.update("A2", [[json.dumps({"progress":"setting", "RowNum": 0})]])
    sheet1.update([["Scrapping Finished"]], "Q1")
    driver.quit()
    print("Saved every data into the Google Sheet successfully.")

if __name__ == "__main__":
    main()
