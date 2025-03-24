from flask_cors import CORS

from app import create_app

app = create_app()
# CORS(app, resources=r'/*')

if __name__ == '__main__':
    # CORS(app)
    # 允许所有来源
    CORS(app, resources={
        r"/*": {
            "origins": "*",  # 允许所有来源
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 支持的方法
            "allow_headers": "*",  # 支持的所有头部信息
            # "supports_credentials": True  # 如果需要支持凭证，则设置为True
        }
    })
    CORS(app)
    app.run(host='0.0.0.0', port=5000)
