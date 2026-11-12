"""
Arquivo de configuração de exemplo para o Portal Power BI
Copie este arquivo para config.py e ajuste as configurações conforme necessário
"""

import os
from datetime import timedelta

class Config:
    """Configurações base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Flask-Login
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Sessão expira em 8 horas
    SESSION_PROTECTION = 'strong'  # Proteção forte de sessão
    
    # Arquivos de dados (em produção, use banco de dados)
    REPORTS_FILE = 'reports.json'
    USERS_FILE = 'users.json'
    PERMISSIONS_FILE = 'permissions.json'
    
    # Configurações de segurança
    MIN_PASSWORD_LENGTH = 6
    REQUIRE_STRONG_PASSWORDS = False  # True para exigir senhas mais complexas
    MAX_LOGIN_ATTEMPTS = 5  # Máximo de tentativas de login (futuro)
    
    # Configurações da aplicação
    REPORTS_PER_PAGE = 20  # Paginação (futuro)
    ALLOWED_DOMAINS = ['powerbi.com', 'app.powerbi.com']  # Domínios permitidos para iframes
    
    # Configurações de email (futuro - para reset de senha)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    FLASK_ENV = 'production'
    REQUIRE_STRONG_PASSWORDS = True
    
    # Use PostgreSQL em produção
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Configurações de segurança mais rigorosas
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}