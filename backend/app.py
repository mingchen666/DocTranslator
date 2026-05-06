from flask_cors import CORS

from app import create_app

app = create_app()

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": "*",
    }
})

# 开发模式启动：python app.py
# 生产模式启动：gunicorn -b 0.0.0.0:5000 -w 4 -k gevent --timeout 120 app:app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
