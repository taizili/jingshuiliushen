#!/bin/bash
cd "$(dirname "$0")"
echo "正在启动网站后台..."
echo ""
echo "  管理后台: http://localhost:8000/admin"
echo "  网站首页: http://localhost:8000"
echo ""
( sleep 1; open "http://localhost:8000/admin" ) &
python3 admin.py
