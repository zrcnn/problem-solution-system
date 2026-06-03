import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 公司信息
    COMPANY_NAME = "杭州盾源科技有限公司"
    SYSTEM_TITLE = "现场问题解决方案管理系统"
    SYSTEM_VERSION = "1.0.0"
    
    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db', 'problems.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 打印数据库URI用于调试
    print(f"Database URI: {SQLALCHEMY_DATABASE_URI}")