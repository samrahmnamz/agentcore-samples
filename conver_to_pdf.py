import markdown
import pdfkit

with open('README.md', 'r') as f:
    html = markdown.markdown(f.read())

pdfkit.from_string(html, 'README.pdf')
