     from playwright.sync_api import sync_playwright

     def handler(event, context):
         with sync_playwright() as p:
             browser = p.chromium.launch(args=["--disable-gpu", "--single-process", "--headless=new"], headless=True)
             page = browser.new_page()
             page.goto("https://stackoverflow.com/questions/9780717/bash-pip-command-not-found")
             print(page.title())
             browser.close()