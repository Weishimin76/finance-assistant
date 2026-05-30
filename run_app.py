# -*- coding: utf-8 -*-
"""
跨境财务助手启动器 - 用于打包EXE
"""
import sys
import os
import subprocess

def main():
    # 获取EXE所在目录
    if getattr(sys, 'frozen', False):
        # 打包后的EXE运行
        app_dir = os.path.dirname(sys.executable)
    else:
        # 直接运行Python脚本
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到应用目录
    os.chdir(app_dir)
    
    # 启动Streamlit
    import streamlit.web.cli as stcli
    sys.argv = ['streamlit', 'run', 'app_secure.py', '--server.headless', 'true']
    stcli.main()

if __name__ == '__main__':
    main()
