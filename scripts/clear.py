import json

from google_form_package import Sheet


def main():
    web_sheet = Sheet()
    sheet1 = web_sheet.get_worksheet("Sheet1")
    sheet2 = web_sheet.get_worksheet("Sheet2")
    process_sheet = web_sheet.get_worksheet("Progress")
    sheet1.update([["Scrapping Finished"]], "S1")
    sheet2.update([["Reporting Finished"]], "E1")
    process_sheet.update("A1", [[json.dumps({"progress":"setting", "UrlNum": 1})]])
    process_sheet.update("A2", [[json.dumps({"progress":"setting", "RowNum": 0})]])
    process_sheet.update("B2", [[json.dumps({"progress":"setting", "RowNum": 1})]])
    process_sheet.update("C2", [[json.dumps({"progress":"setting", "RowNum": 2})]])
    process_sheet.update("D2", [[json.dumps({"progress":"setting", "RowNum": 3})]])
    process_sheet.update("E2", [[json.dumps({"progress":"setting", "RowNum": 4})]])
    process_sheet.update("A3", [[json.dumps({"progress":"setting", "UrlNum": 1})]])
  
if __name__ == "__main__":
    main()
