# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
from datetime import datetime, timedelta
import webbrowser

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta para sessões

# Cria o banco de dados se não existir
def init_db():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS stock (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT NOT NULL,
                 tipo TEXT,
                 quantidade INTEGER,
                 validade TEXT)''')
    conn.commit()
    conn.close()

init_db()

from werkzeug.security import generate_password_hash, check_password_hash

def init_usuarios():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_usuarios()

def criar_utilizador_admin():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    username = 'admin2'
    password_hash = generate_password_hash('4321')  # hash seguro da senha
    try:
        c.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (username, password_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Utilizador já existe.")
    conn.close()

#criar_utilizador_admin()
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['password']

        if not username or not senha:
            flash('Preencha todos os campos!', 'error')
            return render_template('login.html')

        conn = sqlite3.connect('stock.db')
        c = conn.cursor()
        c.execute("SELECT password FROM usuarios WHERE username = ?", (username,))
        resultado = c.fetchone()
        conn.close()

        if resultado and check_password_hash(resultado[0], senha):
            session['autenticado'] = True
            session['username'] = username
            flash('Login realizado com sucesso.')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/')
def index():
    # Filtros
    nome_filtro = request.args.get('nome', '')
    tipo_filtro = request.args.get('tipo', '')
    destaque_filtro = request.args.getlist('destaque')  # lista de destaques


    ordenar_por = request.args.get('ordenar', 'id')
    ordem = request.args.get('ordem', 'asc')

    # Paginação
    pagina = int(request.args.get('pagina', 1))
    por_pagina = 10
    offset = (pagina - 1) * por_pagina

    conn = sqlite3.connect('stock.db')
    c = conn.cursor()

    # Montar a parte WHERE dinamicamente
    where = "WHERE 1=1"
    params = []

    if nome_filtro:
        where += " AND nome LIKE ?"
        params.append(f"%{nome_filtro}%")
    if tipo_filtro:
        where += " AND tipo = ?"
        params.append(tipo_filtro)


    # Obter total de registros (para paginação)
    c.execute(f"SELECT COUNT(*) FROM stock {where}", params)
    total_itens = c.fetchone()[0]
    total_paginas = (total_itens + por_pagina - 1) // por_pagina

    if ordenar_por not in ['id', 'nome', 'tipo', 'quantidade', 'validade']:
        ordenar_por = 'id'
    if ordem not in ['asc', 'desc']:
        ordem = 'asc'

    # Buscar os itens da página atual
    query = f"SELECT * FROM stock {where} ORDER BY {ordenar_por} {ordem.upper()} LIMIT ? OFFSET ?"

    params += [por_pagina, offset]
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    hoje = datetime.today().date()
    validade_limite = hoje + timedelta(days=7)

    itens = []
    for item in rows:
        id_, nome, tipo, quantidade, validade_str = item
        validade_data = None
        try:
            validade_data = datetime.strptime(validade_str, "%Y-%m-%d").date()
        except:
            pass

        destaque = ""
        if validade_data and validade_data < hoje:
            destaque = "expired"
        elif validade_data and validade_data <= validade_limite:
            destaque = "warning"
        elif quantidade is not None and quantidade <= 2:
            destaque = "danger"
        else:
            destaque = ""

        itens.append({
            'id': id_,
            'nome': nome,
            'tipo': tipo,
            'quantidade': quantidade,
            'validade_str': validade_str,
            'destaque': destaque
        })

    if destaque_filtro:
        itens = [item for item in itens if item['destaque'] in destaque_filtro]

    ordenar_proximo = 'desc' if ordem == 'asc' else 'asc'

    return render_template('index.html', itens=itens,
                           nome_filtro=nome_filtro,
                           tipo_filtro=tipo_filtro,
                           destaque_filtro=destaque_filtro,
                           pagina=pagina,
                           total_paginas=total_paginas,
                           ordenar_por=ordenar_por,
                           ordem=ordem,
                           ordenar_proximo=ordenar_proximo)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if not session.get('autenticado'):
        flash("Acesso restrito. Faça login.")
        return redirect(url_for('login'))
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        quantidade = int(request.form['quantidade'])
        validade = formatar_data(request.form['validade'])
        if validade is None and request.form['validade']:  # houve erro no formato
            return "Data inválida. Use o formato YYYY-MM-DD."
        conn = sqlite3.connect('stock.db')
        c = conn.cursor()
        c.execute("INSERT INTO stock (nome, tipo, quantidade, validade) VALUES (?, ?, ?, ?)",
                  (nome, tipo, quantidade, validade))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    if not session.get('autenticado'):
        flash("Acesso restrito. Faça login.")
        return redirect(url_for('login'))
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    if request.method == 'POST':
        nome = request.form['nome']
        tipo = request.form['tipo']
        quantidade = int(request.form['quantidade'])
        validade = formatar_data(request.form['validade'])

        if validade is None and request.form['validade']:
            return "Data inválida. Use o formato YYYY-MM-DD."
        
        c.execute("UPDATE stock SET nome=?, tipo=?, quantidade=?, validade=? WHERE id=?",
                  (nome, tipo, quantidade, validade, item_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute("SELECT * FROM stock WHERE id=?", (item_id,))
        item = c.fetchone()
        conn.close()
        return render_template('edit.html', item=item)

@app.route('/delete/<int:item_id>')
def delete(item_id):
    if not session.get('autenticado'):
        flash("Acesso restrito. Faça login.")
        return redirect(url_for('login'))
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("DELETE FROM stock WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

from flask import make_response
import csv
import io

@app.route('/export')
def export():
    nome_filtro = request.args.get('nome', '')
    tipo_filtro = request.args.get('tipo', '')
    destaque_filtro = request.args.getlist('destaque')

    conn = sqlite3.connect('stock.db')
    c = conn.cursor()

    where = "WHERE 1=1"
    params = []

    if nome_filtro:
        where += " AND nome LIKE ?"
        params.append(f"%{nome_filtro}%")
    if tipo_filtro:
        where += " AND tipo = ?"
        params.append(tipo_filtro)

    c.execute(f"SELECT * FROM stock {where}", params)
    rows = c.fetchall()
    conn.close()

    hoje = datetime.today().date()
    validade_limite = hoje + timedelta(days=7)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nome', 'Tipo', 'Quantidade', 'Validade', 'Destaque'])

    for row in rows:
        id_, nome, tipo, quantidade, validade = row
        try:
            validade_data = datetime.strptime(validade, "%Y-%m-%d").date() if validade else None
        except:
            validade_data = None

        destaque = ""
        if validade_data and validade_data < hoje:
            destaque = "expired"
        elif validade_data and validade_data <= validade_limite:
            destaque = "warning"
        elif quantidade <= 5:
            destaque = "danger"

        if destaque_filtro and destaque != destaque_filtro:
            continue

        writer.writerow([id_, nome, tipo, quantidade, validade, destaque])

    output.seek(0)
    response = make_response(output.getvalue())

    filename = "stock"

    if nome_filtro:
        filename += f"_nome-{nome_filtro.replace(' ', '_')}"
    if tipo_filtro:
        filename += f"_tipo-{tipo_filtro.replace(' ', '_')}"
    for destaque_fltr in destaque_filtro:
        if destaque_fltr == "expired":
            filename += f"_produtosforadavalidade"
        if destaque_fltr == "warning":
            filename += f"_produtosvalidadelimite"
        if destaque_fltr == "danger":
            filename += f"_produtospoucaquantidade"

    filename += ".csv"

    response.headers["Content-Disposition"] = f"attachment; filename={filename}"

    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.clear()
    flash('Sessão terminada.')
    return redirect(url_for('index'))

# Função para validar e formatar a data
def formatar_data(data_str):
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        return data.isoformat()  # retorna "YYYY-MM-DD"
    except ValueError:
        return None  # data inválida
    
if __name__ == '__main__':
    webbrowser.open("http://192.168.10.53:5000")
    app.run(debug=True, host='0.0.0.0')
