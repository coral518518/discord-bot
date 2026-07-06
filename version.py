import sys
from flask import Flask

app = Flask(__name__)

# 1. 启动时直接在控制台/日志打印版本
print(f"\n\n🚀 CURRENT PYTHON VERSION: {sys.version}\n\n", flush=True)

# 2. 必须提供健康检查接口，否则云平台会认为启动失败
@app.route('/health')
@app.route('/')
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
