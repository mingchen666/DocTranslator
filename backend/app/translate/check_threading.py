import threading
from . import rediscon
import db
import sys
def main():
    uuid=sys.argv[1]
    trans=db.get("select * from translate where uuid=%s", uuid)
    api_url=trans['api_url']
    mredis=rediscon.get_conn()
    threading_num=int(mredis.get(api_url))
    print(threading_num)
if __name__ == '__main__':
    main()


