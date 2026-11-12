from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import os
import json
import secrets
import logging
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    app.secret_key = secrets.token_hex(32)
    logging.warning("SECRET_KEY não definida: usando chave temporária (sessões caem a cada reinício)")

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# ===== DADOS EM MEMÓRIA (RESETAM A CADA DEPLOY) =====
# Em produção real, use banco de dados. Para teste/demonstração, funciona perfeitamente.

def load_users():
    """
    Usuários vêm do ambiente/.env, nunca do código.

    PORTAL_USERS: lista JSON, ex.:
      [{"id": "admin-001", "username": "admin", "email": "admin@example.com",
        "password": "senha-forte", "role": "admin"}]
    Alternativa mínima: ADMIN_USERNAME + ADMIN_PASSWORD (+ ADMIN_EMAIL).
    As senhas são convertidas em hash ao carregar e não ficam em texto.
    """
    raw = os.environ.get('PORTAL_USERS')
    entries = []
    if raw:
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError as e:
            logging.error(f"PORTAL_USERS inválido: {e}")
    elif os.environ.get('ADMIN_USERNAME') and os.environ.get('ADMIN_PASSWORD'):
        entries = [{
            'id': 'admin-001',
            'username': os.environ['ADMIN_USERNAME'],
            'email': os.environ.get('ADMIN_EMAIL', ''),
            'password': os.environ['ADMIN_PASSWORD'],
            'role': 'admin',
        }]
    if not entries:
        logging.error("Nenhum usuário configurado (PORTAL_USERS ou ADMIN_USERNAME/ADMIN_PASSWORD)")

    users = []
    for i, e in enumerate(entries, 1):
        users.append({
            'id': e.get('id') or f'user-{i:03d}',
            'username': e['username'],
            'email': e.get('email', ''),
            'password_hash': generate_password_hash(e['password']),
            'role': e.get('role', 'user'),
            'active': e.get('active', True),
        })
    return users


USERS = load_users()

# Relatórios de exemplo
REPORTS = [
    {
        'id': 'report-001',
        'title': 'Relatório Vendedor 1',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000003&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-01T10:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-002',
        'title': 'Relatório Vendedor 2',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000005&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-02T14:30:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-003',
        'title': 'Gerencial',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000006&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',
        'description': '',
        'category': 'Gerencial',
        'active': True,
        'created_at': '2024-01-03T09:15:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-004',
        'title': 'Análise de Meta e Margem',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000007&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',
        'description': '',
        'category': 'Comercial',
        'active': True,
        'created_at': '2024-01-04T16:45:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-005',
        'title': 'Validações Cálculos',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000008&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',
        'description': 'Campanhas de marketing e resultados',
        'category': 'Admin',
        'active': False,
        'created_at': '2024-01-05T11:20:00',
        'created_by': 'admin-001'
    },

    # --- BIs individuais dos vendedores (links para você preencher) ---
    {
        'id': 'report-006',
        'title': 'Relatório Vendedor 3',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000009&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-06T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-007',
        'title': 'Relatório Vendedor 4',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000010&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-07T09:00:00',
        'created_by': 'admin-001'
    },
#    {
#        'id': 'report-008',
#        'title': 'Relatório Vendedor 5',
#        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000011&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
#        'description': '',
#        'category': 'Vendedores',
#        'active': True,
#        'created_at': '2024-01-08T09:00:00',
#        'created_by': 'admin-001'
#    },
    {
        'id': 'report-009',
        'title': 'Relatório Vendedor 6',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000012&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-09T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-010',
        'title': 'Relatório Vendedor 7',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000013&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-10T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-011',
        'title': 'Relatório Vendedor 8',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000014&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-012',
        'title': 'Auditoria de Frete',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000015&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Logística',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-013',
        'title': 'Análise de Estoque',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000016&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Comercial',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-014',
        'title': 'Atacado',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000017&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Atacado',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-015',
        'title': 'Logística',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000018&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Logística',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-016',
        'title': 'Relatório Vendedor 9',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000019&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-017',
        'title': 'Relatório Vendedor 10',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000020&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-018',
        'title': 'SLA Logística',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000021&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Logística',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-019',
        'title': 'Relatório Vendedor 11',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000022&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-020',
        'title': 'Análise de Reversa',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000023&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Logística',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-021',
        'title': 'Validações',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000008&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Admin',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-022',
        'title': 'Relatório Vendedor 12',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000024&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    },
    {
        'id': 'report-023',
        'title': 'Relatório Vendedor 13',
        'iframe_url': 'https://app.powerbi.com/reportEmbed?reportId=00000000-0000-0000-0000-000000000025&autoAuth=true&ctid=00000000-0000-0000-0000-000000000004',  # TODO: inserir link
        'description': '',
        'category': 'Vendedores',
        'active': True,
        'created_at': '2024-01-11T09:00:00',
        'created_by': 'admin-001'
    }
]

# Permissões dos usuários
PERMISSIONS = {
    # Usuário básico com acesso a TODOS os BIs de vendedores
    'user-001': {
        'type': 'specific',
        'reports': ['report-014', 'report-005'],
        'categories': ['Comercial', 'Vendedores', 'Atacado','Admin'],
        'all_access': False
    },

    # Cada vendedor acessa somente o próprio BI
    'user-002': {
        'type': 'specific',
        'reports': ['report-001'],
        'categories': [],
        'all_access': False
    },
    'user-003': {
        'type': 'specific',
        'reports': ['report-006'],
        'categories': [],
        'all_access': False
    },
    'user-004': {
        'type': 'specific',
        'reports': ['report-007'],
        'categories': [],
        'all_access': False
    },
#    'user-005': {
#        'type': 'specific',
#        'reports': ['report-008'],
#        'categories': [],
#        'all_access': False
#    },
    'user-006': {
        'type': 'specific',
        'reports': ['report-009'],
        'categories': [],
        'all_access': False
    },
    'user-007': {
        'type': 'specific',
        'reports': ['report-002'],
        'categories': [],
        'all_access': False
    },
    'user-008': {
        'type': 'specific',
        'reports': ['report-010'],
        'categories': [],
        'all_access': False
    },
    'user-009': {
        'type': 'specific',
        'reports': ['report-011'],
        'categories': [],
        'all_access': False
    },
    'user-010': {
        'type': 'specific',
        'reports': ['report-012','report-015','report-018'],
        'categories': [],
        'all_access': False
    },
    'user-011': {
        'type': 'specific',
        'reports': ['report-012', 'report-004'],
        'categories': ['Comercial','Logística'],
        'all_access': False
    },
    'user-012': {
        'type': 'specific',
        'reports': [],
        'categories': ['Comercial','Atacado', 'Gerencial'],
        'all_access': False
    },
    'user-013': {
        'type': 'specific',
        'reports': ['report-012','report-015'],
        'categories': [],
        'all_access': False
    },
    'user-014': {
        'type': 'specific',
        'reports': [],
        'categories': ['Comercial','Atacado','Logística'],
        'all_access': False
    },
    'user-015': {
        'type': 'specific',
        'reports': [],
        'categories': ['Atacado'],
        'all_access': False
    },
    'user-016': {
        'type': 'specific',
        'reports': ['report-015'],
        'categories': ['Comercial','Atacado'],
        'all_access': False
    },
    'user-017': {
        'type': 'specific',
        'reports': ['report-016'],
        'categories': [],
        'all_access': False
    },
    'user-018': {
        'type': 'specific',
        'reports': ['report-017'],
        'categories': [],
        'all_access': False
    },
    'user-019': {
        'type': 'specific',
        'reports': ['report-019'],
        'categories': [],
        'all_access': False
    },
    'user-020': {
        'type': 'specific',
        'reports': ['report-012','report-015'],
        'categories': ['Logística'],
        'all_access': False
    },
    'user-021': {
        'type': 'specific',
        'reports': ['report-020'],
        'categories': [],
        'all_access': False
    },
    'user-022': {
        'type': 'specific',
        'reports': ['report-022'],
        'categories': [],
        'all_access': False
    },
    'user-023': {
        'type': 'specific',
        'reports': ['report-023'],
        'categories': [],
        'all_access': False
    }
}

# ===== MODELO DE USUÁRIO =====

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, role='user', active=True):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.active = active
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    for user_data in USERS:
        if user_data['id'] == user_id:
            return User(**user_data)
    return None

# ===== DECORATORS =====

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ===== FUNÇÕES AUXILIARES =====

def get_user_reports():
    """Retorna apenas os relatórios que o usuário atual pode ver"""
    if current_user.is_admin():
        return REPORTS
    
    user_permissions = PERMISSIONS.get(current_user.id, {})
    
    if not user_permissions:
        return []
    
    if user_permissions.get('all_access', False):
        return [r for r in REPORTS if r.get('active', True)]
    
    allowed_reports = []
    
    for report in REPORTS:
        if not report.get('active', True):
            continue
            
        report_allowed = False
        
        # Verificar por categoria
        if report['category'] in user_permissions.get('categories', []):
            report_allowed = True
        
        # Verificar por relatório específico
        if report['id'] in user_permissions.get('reports', []):
            report_allowed = True
            
        if report_allowed:
            allowed_reports.append(report)
    
    return allowed_reports

def can_access_report(report_id):
    """Verifica se o usuário atual pode acessar um relatório específico"""
    if current_user.is_admin():
        return True
    
    user_reports = get_user_reports()
    return any(report['id'] == report_id for report in user_reports)

def get_available_categories():
    """Retorna lista de categorias disponíveis"""
    categories = list(set(report['category'] for report in REPORTS if report.get('category')))
    return sorted(categories)

def find_user_by_id(user_id):
    """Encontra usuário por ID"""
    for user in USERS:
        if user['id'] == user_id:
            return user
    return None

def find_report_by_id(report_id):
    """Encontra relatório por ID"""
    for report in REPORTS:
        if report['id'] == report_id:
            return report
    return None

# ===== ROTAS =====

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        for user_data in USERS:
            if (user_data['username'] == username or user_data['email'] == username) and user_data['active']:
                user = User(**user_data)
                if user.check_password(password):
                    login_user(user, remember=request.form.get('remember'))
                    next_page = request.args.get('next')
                    flash(f'Bem-vindo, {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('index'))
        
        flash('Usuário ou senha incorretos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    reports = get_user_reports()
    return render_template('index.html', reports=reports)

@app.route('/admin')
@login_required
@admin_required
def admin():
    return render_template('admin.html', reports=REPORTS)

@app.route('/users')
@login_required
@admin_required
def manage_users():
    categories = get_available_categories()
    return render_template('users.html', users=USERS, permissions=PERMISSIONS, reports=REPORTS, categories=categories)

@app.route('/add_user', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if not username or not email or not password:
        flash('Todos os campos são obrigatórios!', 'error')
        return redirect(url_for('manage_users'))
    
    # Verificar se já existe
    for user in USERS:
        if user['username'] == username or user['email'] == email:
            flash('Usuário ou email já existe!', 'error')
            return redirect(url_for('manage_users'))
    
    new_user = {
        'id': str(uuid.uuid4()),
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': role,
        'active': True
    }
    
    USERS.append(new_user)
    print(f"Usuário criado: {username} ({role})")
    flash('Usuário criado com sucesso!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/toggle_user/<user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = find_user_by_id(user_id)
    if user:
        user['active'] = not user.get('active', True)
        status = "ativado" if user['active'] else "desativado"
        print(f"Usuário {user['username']} {status}")
    
    return redirect(url_for('manage_users'))

@app.route('/delete_user/<user_id>')
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Você não pode excluir sua própria conta!', 'error')
        return redirect(url_for('manage_users'))
    
    global USERS, PERMISSIONS
    
    # Encontrar e remover usuário
    user_to_remove = None
    for i, user in enumerate(USERS):
        if user['id'] == user_id:
            user_to_remove = USERS.pop(i)
            break
    
    # Remover permissões
    if user_id in PERMISSIONS:
        del PERMISSIONS[user_id]
    
    if user_to_remove:
        print(f"Usuário {user_to_remove['username']} removido")
        flash('Usuário removido com sucesso!', 'success')
    
    return redirect(url_for('manage_users'))

@app.route('/manage_permissions/<user_id>', methods=['POST'])
@login_required
@admin_required
def manage_permissions(user_id):
    permission_type = request.form.get('permission_type', 'none')
    
    user_permissions = {
        "type": permission_type,
        "reports": [],
        "categories": [],
        "all_access": False
    }
    
    if permission_type == 'all':
        user_permissions['all_access'] = True
    elif permission_type == 'category':
        user_permissions['categories'] = request.form.getlist('categories')
    elif permission_type == 'specific':
        user_permissions['reports'] = request.form.getlist('reports')
    elif permission_type == 'mixed':
        user_permissions['categories'] = request.form.getlist('categories')
        user_permissions['reports'] = request.form.getlist('reports')
    
    PERMISSIONS[user_id] = user_permissions
    
    user = find_user_by_id(user_id)
    username = user['username'] if user else 'Desconhecido'
    print(f"Permissões atualizadas para {username}: {permission_type}")
    
    flash('Permissões atualizadas com sucesso!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/get_user_permissions/<user_id>')
@login_required
@admin_required
def get_user_permissions(user_id):
    permissions = PERMISSIONS.get(user_id, {
        "type": "none",
        "reports": [],
        "categories": [],
        "all_access": False
    })
    return jsonify(permissions)

@app.route('/add_report', methods=['POST'])
@login_required
@admin_required
def add_report():
    title = request.form.get('title')
    iframe_url = request.form.get('iframe_url')
    description = request.form.get('description', '')
    category = request.form.get('category', 'Geral')
    
    if not title or not iframe_url:
        flash('Título e URL do iframe são obrigatórios!', 'error')
        return redirect(url_for('admin'))
    
    if 'powerbi.com' not in iframe_url and 'app.powerbi.com' not in iframe_url:
        flash('Por favor, insira uma URL válida do Power BI', 'error')
        return redirect(url_for('admin'))
    
    new_report = {
        'id': str(uuid.uuid4()),
        'title': title,
        'iframe_url': iframe_url,
        'description': description,
        'category': category,
        'created_at': datetime.now().isoformat(),
        'created_by': current_user.id,
        'active': True
    }
    
    REPORTS.append(new_report)
    print(f"Relatório criado: {title} ({category})")
    flash('Relatório adicionado com sucesso!', 'success')
    return redirect(url_for('admin'))

@app.route('/edit_report/<report_id>', methods=['POST'])
@login_required
@admin_required
def edit_report(report_id):
    report = find_report_by_id(report_id)
    if report:
        old_title = report['title']
        report['title'] = request.form.get('title', report['title'])
        report['iframe_url'] = request.form.get('iframe_url', report['iframe_url'])
        report['description'] = request.form.get('description', report['description'])
        report['category'] = request.form.get('category', report['category'])
        report['updated_at'] = datetime.now().isoformat()
        report['updated_by'] = current_user.id
        print(f"Relatório editado: {old_title} -> {report['title']}")
    
    flash('Relatório atualizado com sucesso!', 'success')
    return redirect(url_for('admin'))

@app.route('/delete_report/<report_id>')
@login_required
@admin_required
def delete_report(report_id):
    global REPORTS, PERMISSIONS
    
    # Encontrar e remover relatório
    report_to_remove = None
    for i, report in enumerate(REPORTS):
        if report['id'] == report_id:
            report_to_remove = REPORTS.pop(i)
            break
    
    # Remover das permissões de todos os usuários
    for user_id in PERMISSIONS:
        if report_id in PERMISSIONS[user_id].get('reports', []):
            PERMISSIONS[user_id]['reports'].remove(report_id)
    
    if report_to_remove:
        print(f"Relatório removido: {report_to_remove['title']}")
        flash('Relatório removido com sucesso!', 'success')
    
    return redirect(url_for('admin'))

@app.route('/toggle_report/<report_id>')
@login_required
@admin_required
def toggle_report(report_id):
    report = find_report_by_id(report_id)
    if report:
        report['active'] = not report.get('active', True)
        status = "ativado" if report['active'] else "desativado"
        print(f"Relatório {report['title']} {status}")
    
    return redirect(url_for('admin'))

@app.route('/report/<report_id>')
@login_required
def view_report(report_id):
    if not can_access_report(report_id):
        flash('Você não tem permissão para acessar este relatório.', 'error')
        return redirect(url_for('index'))
    
    report = find_report_by_id(report_id)
    if report and report.get('active', True):
        print(f"{current_user.username} acessou relatório: {report['title']}")
        return render_template('report.html', report=report)
    
    flash('Relatório não encontrado!', 'error')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user_permissions = PERMISSIONS.get(current_user.id, {})
    reports = get_user_reports()
    return render_template('profile.html', user_reports=reports, user_permissions=user_permissions)

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Senha atual incorreta!', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('Nova senha e confirmação não conferem!', 'error')
        return redirect(url_for('profile'))
    
    if len(new_password) < 6:
        flash('Nova senha deve ter pelo menos 6 caracteres!', 'error')
        return redirect(url_for('profile'))
    
    # Atualizar senha do usuário
    user = find_user_by_id(current_user.id)
    if user:
        user['password_hash'] = generate_password_hash(new_password)
        print(f"Senha alterada para usuário: {current_user.username}")
        flash('Senha alterada com sucesso!', 'success')
    
    return redirect(url_for('profile'))

@app.route('/api/reports')
@login_required
def api_reports():
    reports = get_user_reports()
    return jsonify(reports)

@app.route('/health')
def health():
    return {
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'users_count': len(USERS),
        'reports_count': len(REPORTS),
        'active_reports': len([r for r in REPORTS if r.get('active', True)]),
        'version': '1.0.0'
    }

if __name__ == '__main__':
    print("Iniciando Portal Power BI")
    print("Dados em memória - Configuração simplificada")
    print("Usuários padrão:")
    print("   - admin / admin123 (Administrador)")
    print("   - usuario / user123 (Usuário básico)")
    print("   - gerente / gerente123 (Usuário com mais permissões)")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')










