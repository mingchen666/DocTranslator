import openai
import sys
import getopt
import pdf

def main():
    pdf_path=sys.argv[1]
    result=pdf.is_scanned_pdf(pdf_path)
    print(result)

if __name__ == '__main__':
    main()


