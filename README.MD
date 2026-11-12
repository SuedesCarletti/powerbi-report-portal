# Portal Power BI

Um portal elegante e responsivo para embedar e gerenciar seus relatórios do Power BI. Desenvolvido em Python/Flask e otimizado para deployment no Railway.

## 🚀 Características

- **Interface Moderna**: Design responsivo com Bootstrap 5 e animações suaves
- **Gerenciamento Completo**: Adicione, edite, ative/desative e remova relatórios
- **Categorização**: Organize seus relatórios por categorias personalizadas
- **Visualização Otimizada**: 
  - Modo tela cheia
  - Controles de atualização
  - Links diretos para Power BI
  - Atalhos de teclado (F11, F5, ESC)
- **Responsivo**: Funciona perfeitamente em desktop, tablet e mobile
- **Deploy Simples**: Configurado para Railway com deploy automático

## 📁 Estrutura do Projeto

```
portal-powerbi/
├── app.py                 # Aplicação Flask principal
├── requirements.txt       # Dependências Python
├── Procfile              # Configuração para Railway
├── railway.toml          # Configurações do Railway
├── templates/            # Templates HTML
│   ├── base.html         # Layout base
│   ├── index.html        # Página principal
│   ├── admin.html        # Administração
│   └── report.html       # Visualização de relatório
└── reports.json          # Armazenamento dos relatórios (criado automaticamente)
```

## 🛠️ Instalação Local

### Pré-requisitos
- Python 3.8+ instalado
- Git instalado

### Passos

1. **Clone o repositório** (ou crie os arquivos manualmente):
```bash
mkdir portal-powerbi
cd portal-powerbi
```

2. **Crie um ambiente virtual**:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

4. **Execute a aplicação**:
```bash
python app.py
```

5. **Acesse no navegador**:
```
http://localhost:5000
```

## 🚀 Deploy no Railway

### Método 1: Deploy Direto

1. **Crie uma conta no Railway**: https://railway.app
2. **Clique em "New Project"**
3. **Selecione "Deploy from GitHub repo"**
4. **Conecte seu repositório** com os arquivos do projeto
5. **O deploy será automático!**

### Método 2: Railway CLI

1. **Instale o Railway CLI**:
```bash
npm install -g @railway/cli
```

2. **Faça login**:
```bash
railway login
```

3. **Inicialize o projeto**:
```bash
railway init
```

4. **Faça o deploy**:
```bash
railway up
```

### Variáveis de Ambiente

O Railway configurará automaticamente:
- `PORT`: Porta da aplicação
- `SECRET_KEY`: Chave secreta (gerada automaticamente)
- `FLASK_ENV`: Ambiente de produção

## 📊 Como Usar

### 1. Obtendo URLs do Power BI

Para embedar relatórios do Power BI, você precisa da URL de embed:

1. **Acesse seu relatório no Power BI**
2. **Clique em "Arquivo" > "Embedar" > "Site ou Portal"**
3. **Copie a URL que aparece no código iframe**
4. **Cole essa URL no campo "URL do Iframe" no portal**

### 2. Adicionando Relatórios

1. **Acesse a página de Administração**
2. **Clique em "Novo Relatório"**
3. **Preencha os campos**:
   - **Título**: Nome que aparecerá no portal
   - **URL do Iframe**: URL de embed do Power BI
   - **Descrição**: Descrição opcional
   - **Categoria**: Para organizar os relatórios
4. **Clique em "Salvar Relatório"**

### 3. Gerenciando Relatórios

Na página de administração você pode:
- ✏️ **Editar**: Modificar informações do relatório
- 👁️ **Visualizar**: Abrir o relatório
- ⏸️ **Ativar/Desativar**: Controlar visibilidade
- 🗑️ **Excluir**: Remover permanentemente

### 4. Visualizando Relatórios

- **Filtros**: Use os botões de categoria para filtrar
- **Tela Cheia**: Clique no botão flutuante ou pressione F11
- **Atualizar**: Pressione F5 ou use o botão de refresh
- **Compartilhar**: Copie o link direto para o relatório

## ⌨️ Atalhos de Teclado

- **F11**: Entrar/sair do modo tela cheia
- **F5**: Atualizar relatório
- **ESC**: Sair do modo tela cheia

## 🔧 Personalização

### Modificando Cores

Edite as variáveis CSS no arquivo `templates/base.html`:

```css
:root {
    --primary-color: #0078d4;      /* Azul principal */
    --secondary-color: #106ebe;    /* Azul secundário */
    --success-color: #107c10;      /* Verde */
    --warning-color: #ff8c00;      /* Laranja */
    --danger-color: #d13438;       /* Vermelho */
    --bg-color: #f8f9fa;          /* Fundo */
}
```

### Adicionando Funcionalidades

A aplicação foi estruturada para fácil extensão:
- **app.py**: Adicione novas rotas
- **templates/**: Modifique a interface
- **reports.json**: Dados são armazenados em JSON (considere banco de dados para produção)

## 🗃️ Banco de Dados

Atualmente, os dados são armazenados em arquivo JSON. Para produção, considere migrar para PostgreSQL:

```python
# Exemplo com SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

class Report(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    iframe_url = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 🔐 Segurança

### **Recursos Implementados**
- **Hash de Senhas**: Senhas são criptografadas com Werkzeug
- **Autenticação de Sessão**: Flask-Login gerencia sessões seguras
- **Controle de Acesso**: Decorators protegem rotas administrativas
- **Validação de Entrada**: Sanitização de dados do usuário
- **HTTPS**: Railway oferece SSL/TLS automaticamente

### **Para Produção, Considere**
- **Autenticação 2FA**: Implementar autenticação de dois fatores
- **Políticas de Senha**: Requisitos mais rigorosos (maiúsculas, números, símbolos)
- **Logs de Auditoria**: Rastreamento de ações dos usuários
- **Rate Limiting**: Proteção contra ataques de força bruta
- **Integração SSO**: Single Sign-On com Active Directory/OAuth

### **Configurações Recomendadas**
```python
# Variáveis de ambiente para produção
SECRET_KEY=sua-chave-super-secreta-aleatoria
FLASK_ENV=production
DATABASE_URL=postgresql://...  # Use PostgreSQL em produção
```

## 🆘 Solução de Problemas

### Erro ao carregar iframe
- Verifique se a URL do Power BI está correta
- Confirme se o relatório está publicado e compartilhado
- Teste a URL diretamente no navegador

### Deploy falha no Railway
- Verifique se todos os arquivos estão no repositório
- Confirme se o `requirements.txt` está correto
- Veja os logs no painel do Railway

### Relatórios não aparecem
- Verifique se estão marcados como "Ativo"
- Confirme se não há erros de JavaScript no console
- Teste em modo privado/incógnito

## 📝 Licença

Este projeto é open source e está disponível sob a licença MIT.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Submeter pull requests

---

**Desenvolvido com ❤️ para facilitar o acesso aos seus relatórios Power BI**