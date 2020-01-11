#!/usr/bin/python3

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Rowan's Songs").get_worksheet(0)
records = sheet.get_all_records()
print(records)
