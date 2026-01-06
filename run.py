#!/usr/bin/env python
"""开发服务器启动脚本"""

if __name__ == '__main__':
    from app.http.app import app
    app.run(debug=True, host='0.0.0.0', port=8000)
