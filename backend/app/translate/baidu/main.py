import json

import requests
import random
import hashlib



def baidu_translate(
        text: str,
        appid: str,
        app_key: str,
        from_lang: str = 'auto',
        to_lang: str = 'en',
        use_term_base: bool = False,
) -> str:
    """
    参数:
        text: 要翻译的文本（多行文本用换行符分隔）
        appid: 百度API的APP ID
        key: 百度API的密钥
        from_lang: 源语言代码（默认auto自动检测）
        to_lang: 目标语言代码（默认en英语）
        use_term_base: 是否启用术语库（通过needIntervene=1控制）

    """
    # 1. 生成签名参数
    salt = str(random.randint(32768, 65536))
    sign_str = appid + text + salt + app_key
    sign = hashlib.md5(sign_str.encode()).hexdigest()

    # 2. 构造请求参数
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': appid,
        'salt': salt,
        'sign': sign,
    }
    if use_term_base:
        params['needIntervene'] = 1  # 启用术语库

    # 3. 发送请求
    try:
        response = requests.get(
            "https://fanyi-api.baidu.com/api/trans/vip/translate",
            params=params,
            timeout=60
        )
        result = response.json()

        if 'error_code' in result:
            raise Exception(f"百度API错误 {result['error_code']}: {result['error_msg']}")

        # 4. 拼接翻译结果（保留原文换行结构）
        return '\n'.join(item['dst'] for item in result['trans_result'])

    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("百度API返回数据解析失败")

