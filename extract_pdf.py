import pdfplumber

pdf_path = r'c:\Users\id032400\Documents\GitHub\Agent_based_dev\DiWeiWei_Nano_Market\doc\seed\SA2_70476607.pdf'
output_path = r'c:\Users\id032400\Documents\GitHub\Agent_based_dev\DiWeiWei_Nano_Market\doc\seed\SA2_70476607.txt'

with pdfplumber.open(pdf_path) as pdf:
    text = ''
    for page_num, page in enumerate(pdf.pages):
        text += f'=== PAGE {page_num + 1} ===\n'
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text
        text += '\n\n'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f"PDF converted successfully to {output_path}")
