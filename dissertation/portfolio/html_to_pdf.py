import asyncio
from pyppeteer import launch
import os

async def html_to_pdf():
    html_path = os.path.abspath("rolebox_rolefield-ui.html")
    pdf_path = os.path.abspath("rolebox_rolefield-ui.pdf")

    print(f"Converting: {html_path}")
    print(f"Output: {pdf_path}")

    browser = await launch(headless=True)
    page = await browser.newPage()

    # Load the HTML file
    await page.goto(f'file:///{html_path}', {'waitUntil': 'networkidle0'})

    # Set viewport to capture full page
    await page.setViewport({'width': 1400, 'height': 900})

    # Generate PDF - A4 landscape to capture the UI nicely
    await page.pdf({
        'path': pdf_path,
        'format': 'A4',
        'landscape': True,
        'printBackground': True,
        'margin': {
            'top': '10mm',
            'bottom': '10mm',
            'left': '10mm',
            'right': '10mm'
        }
    })

    await browser.close()
    print(f"PDF created successfully: {pdf_path}")

asyncio.get_event_loop().run_until_complete(html_to_pdf())
