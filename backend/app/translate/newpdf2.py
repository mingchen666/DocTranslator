from pypdf import PdfWriter, PdfReader

output = PdfWriter('out.pdf')
input1 = PdfReader("document1.pdf", "rb")

    # add page 1 from input1 to output document, unchanged
output.add_page(input1.get_page(0))

    # add page 2 from input1, but rotated clockwise 90 degrees
output.add_page(input1.get_page(1).rotate(90))

    # add page 3 from input1, rotated the other way:
output.add_page(input1.get_page(2).rotate(180))
output.add_page(input1.get_page(3).rotate(270))
output.write('out.pdf')

from pypdf import PdfWriter, PdfReader
from pypdf.generic import (
    ArrayObject,
    ContentStream,
    DictionaryObject,
    EncodedStreamObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    PdfObject,
    RectangleObject,
    StreamObject,
    TextStringObject,
    is_null_or_none,
)
output = PdfWriter()
input1 = PdfReader("document1.pdf", "rb")

page_nums=input1.get_num_pages()
for page_num in range(page_nums):
    page= input1.get_page(page_num)
    original_content=page.extract_text(extraction_mode="layout", layout_mode_strip_rotated=True)
    print(page['/Contents'])
    print(original_content)