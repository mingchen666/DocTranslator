import sys
import getopt
import requests
import logging
import logging.config

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

def main():
    token=sys.argv[1]
    url = 'https://v2.doc2x.noedgeai.com/api/v2/parse/status?uid=test'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(url, headers=headers)
    # 输出响应内容
    print(response.status_code)

if __name__ == '__main__':
    main()


