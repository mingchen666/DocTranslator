import openai
import sys
import getopt
from . import to_translate

def main():
    api_url=sys.argv[1]
    api_key=sys.argv[2]
    model=sys.argv[3]

    # 设置OpenAI API
    to_translate.init_openai(api_url, api_key)
    message=to_translate.check(model)
    print(message)

if __name__ == '__main__':
    main()


