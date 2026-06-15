import sqlite3
import os
import secrets

# Caminho absoluto para o banco, baseado na localização deste arquivo.
# Garante que funcione independente de onde o Streamlit for executado.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Em produção (Docker/EasyPanel) o caminho aponta para um volume persistente
# via a variável de ambiente GLICUIDADO_DB_PATH; localmente usa a pasta database/.
DB_PATH = os.environ.get(
    "GLICUIDADO_DB_PATH",
    os.path.join(BASE_DIR, "database", "glicuidado.db"),
)


def conectar():
    # Garante que o diretório do banco exista (importante para volumes montados).
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _adicionar_coluna_se_ausente(cursor, tabela, coluna, definicao):
    """Adiciona uma coluna a uma tabela existente apenas se ela ainda não existir.

    Mantém compatibilidade com bancos criados antes desta versão (a VPS já tem
    dados), evitando perda de informação ao introduzir novos campos.
    """
    colunas = [row[1] for row in cursor.execute(f"PRAGMA table_info({tabela})").fetchall()]
    if coluna not in colunas:
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def criar_tabela():

    conn = conectar()

    cursor = conn.cursor()

    # Tabela de usuários (login)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome_exibicao TEXT,

        funcao TEXT,

        tipo TEXT DEFAULT 'Paciente',

        email TEXT NOT NULL UNIQUE,

        senha_hash TEXT NOT NULL,

        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # Tabela do perfil do paciente, vinculada ao usuário (1:1)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paciente(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario_id INTEGER NOT NULL UNIQUE,

        responsavel_id INTEGER,

        nome TEXT NOT NULL,

        data_nascimento TEXT,

        genero TEXT,

        peso REAL,

        altura REAL,

        status TEXT DEFAULT 'Ativo',

        numero_sus TEXT,

        medicacoes TEXT,

        foto BLOB,

        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)

    )
    """)

    # Tabela de medições de glicemia, vinculada ao usuário
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS glicemia(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        usuario_id INTEGER NOT NULL,

        glicemia REAL NOT NULL,

        medicacao INTEGER NOT NULL,

        medicacoes_utilizadas TEXT,

        medicacao_nome TEXT,

        medicacao_dosagem TEXT,

        atividade INTEGER NOT NULL,

        jejum INTEGER NOT NULL DEFAULT 1,

        refeicao TEXT,

        data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)

    )
    """)

    # Tabela de sessões persistentes (mantém o login após F5 / reload)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessoes(

        token TEXT PRIMARY KEY,

        usuario_id INTEGER NOT NULL,

        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)

    )
    """)

    # Migração: adiciona colunas em bancos criados antes desta versão, sem
    # apagar nada (a VPS já tem dados de usuários).
    _adicionar_coluna_se_ausente(cursor, "usuarios", "funcao", "TEXT")
    _adicionar_coluna_se_ausente(cursor, "usuarios", "tipo", "TEXT DEFAULT 'Paciente'")

    _adicionar_coluna_se_ausente(cursor, "paciente", "responsavel_id", "INTEGER")
    _adicionar_coluna_se_ausente(cursor, "paciente", "genero", "TEXT")
    _adicionar_coluna_se_ausente(cursor, "paciente", "peso", "REAL")
    _adicionar_coluna_se_ausente(cursor, "paciente", "altura", "REAL")
    _adicionar_coluna_se_ausente(cursor, "paciente", "status", "TEXT DEFAULT 'Ativo'")

    _adicionar_coluna_se_ausente(cursor, "glicemia", "jejum", "INTEGER NOT NULL DEFAULT 1")
    _adicionar_coluna_se_ausente(cursor, "glicemia", "refeicao", "TEXT")
    _adicionar_coluna_se_ausente(cursor, "glicemia", "medicacao_nome", "TEXT")
    _adicionar_coluna_se_ausente(cursor, "glicemia", "medicacao_dosagem", "TEXT")

    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# PERFIL DO PACIENTE (por usuário)
# --------------------------------------------------------------------------

def obter_paciente(usuario_id):
    """Retorna o perfil do paciente vinculado ao usuário, ou None se ainda não criado."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, data_nascimento, genero, peso, altura, status,
               numero_sus, medicacoes, foto, responsavel_id
        FROM paciente
        WHERE usuario_id = ?
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "nome": row[1],
        "data_nascimento": row[2] or "",
        "genero": row[3] or "",
        "peso": row[4],
        "altura": row[5],
        "status": row[6] or "Ativo",
        "numero_sus": row[7] or "",
        "medicacoes": row[8] or "",
        "foto": row[9],
        "responsavel_id": row[10]
    }


def salvar_paciente(usuario_id, nome, data_nascimento, numero_sus, medicacoes,
                    genero=None, peso=None, altura=None, status="Ativo", foto=None,
                    responsavel_id=None):
    """Insere ou atualiza o perfil do paciente vinculado ao usuário.

    Se `foto` for None, a foto existente (se houver) é preservada. O vínculo
    `responsavel_id` (enfermeiro dono da ficha) é definido apenas na criação e
    nunca sobrescrito por atualizações.
    """

    conn = conectar()
    cursor = conn.cursor()

    existente = obter_paciente(usuario_id)

    if existente is None:
        cursor.execute("""
            INSERT INTO paciente(
                usuario_id, responsavel_id, nome, data_nascimento, genero, peso,
                altura, status, numero_sus, medicacoes, foto
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, (usuario_id, responsavel_id, nome, data_nascimento, genero, peso,
              altura, status, numero_sus, medicacoes, foto))
    else:
        if foto is None:
            cursor.execute("""
                UPDATE paciente
                SET nome=?, data_nascimento=?, genero=?, peso=?, altura=?,
                    status=?, numero_sus=?, medicacoes=?
                WHERE usuario_id=?
            """, (nome, data_nascimento, genero, peso, altura,
                  status, numero_sus, medicacoes, usuario_id))
        else:
            cursor.execute("""
                UPDATE paciente
                SET nome=?, data_nascimento=?, genero=?, peso=?, altura=?,
                    status=?, numero_sus=?, medicacoes=?, foto=?
                WHERE usuario_id=?
            """, (nome, data_nascimento, genero, peso, altura,
                  status, numero_sus, medicacoes, foto, usuario_id))

    conn.commit()
    conn.close()


def listar_pacientes_do_responsavel(responsavel_id):
    """Lista as fichas de pacientes administradas por um profissional.

    Retorna uma lista de dicts com o usuario_id (chave usada pelas medições),
    nome, status e email de login de cada paciente vinculado ao responsável.
    """

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.usuario_id, p.nome, p.status, u.email
        FROM paciente p
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE p.responsavel_id = ?
        ORDER BY p.nome COLLATE NOCASE
    """, (responsavel_id,))

    linhas = cursor.fetchall()
    conn.close()

    return [
        {
            "usuario_id": linha[0],
            "nome": linha[1],
            "status": linha[2] or "Ativo",
            "email": linha[3],
        }
        for linha in linhas
    ]


# --------------------------------------------------------------------------
# MEDIÇÕES DE GLICEMIA (por usuário)
# --------------------------------------------------------------------------

def obter_ultimo_registro(usuario_id):
    """Retorna o último registro de medição do usuário, ou None se não houver."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT glicemia, medicacao, medicacoes_utilizadas, atividade, data_registro
        FROM glicemia
        WHERE usuario_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "glicemia": row[0],
        "medicacao": row[1],
        "medicacoes_utilizadas": row[2] or "",
        "atividade": row[3],
        "data_registro": row[4]
    }


def inserir_medicao(usuario_id, glicemia, medicacao, medicacao_nome, medicacao_dosagem,
                    atividade, jejum, refeicao, data_registro=None):
    """Insere uma nova medição. Se `data_registro` for None, usa o momento atual.

    Quando o paciente tomou medicação, `medicacao_nome` e `medicacao_dosagem`
    guardam o nome e a dosagem administrada; caso contrário ficam vazios.
    """

    conn = conectar()
    cursor = conn.cursor()

    if data_registro is None:
        cursor.execute(
            """
            INSERT INTO glicemia(
                usuario_id, glicemia, medicacao, medicacao_nome, medicacao_dosagem,
                atividade, jejum, refeicao
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (usuario_id, glicemia, medicacao, medicacao_nome, medicacao_dosagem,
             atividade, jejum, refeicao)
        )
    else:
        cursor.execute(
            """
            INSERT INTO glicemia(
                usuario_id, glicemia, medicacao, medicacao_nome, medicacao_dosagem,
                atividade, jejum, refeicao, data_registro
            )
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (usuario_id, glicemia, medicacao, medicacao_nome, medicacao_dosagem,
             atividade, jejum, refeicao, data_registro)
        )

    conn.commit()
    conn.close()


def obter_ultimas_medicoes(usuario_id, limite=5):
    """Retorna as últimas `limite` medições do usuário, mais recentes primeiro."""

    conn = conectar()

    import pandas as pd

    df = pd.read_sql(
        """
        SELECT glicemia, medicacao, medicacoes_utilizadas, atividade,
               jejum, refeicao, data_registro
        FROM glicemia
        WHERE usuario_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        conn,
        params=(usuario_id, limite)
    )

    conn.close()

    return df


# --------------------------------------------------------------------------
# AUTENTICAÇÃO DE USUÁRIOS
# --------------------------------------------------------------------------

def criar_usuario(email, senha_hash, nome_exibicao="", funcao="", tipo="Paciente"):
    """Cria um novo usuário. Retorna o id criado, ou None se email já existe.

    `tipo` é 'Paciente' (gerencia o próprio histórico) ou 'Profissional'
    (enfermeiro/cuidador que administra vários pacientes).
    """

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios(nome_exibicao, funcao, tipo, email, senha_hash)
            VALUES(?,?,?,?,?)
        """, (nome_exibicao, funcao, tipo, email, senha_hash))

        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None

    finally:
        conn.close()


def obter_usuario_por_email(email):
    """Retorna dados do usuário pelo email, ou None se não existir."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome_exibicao, funcao, tipo, email, senha_hash
        FROM usuarios
        WHERE email = ?
    """, (email,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "nome_exibicao": row[1],
        "funcao": row[2] or "",
        "tipo": row[3] or "Paciente",
        "email": row[4],
        "senha_hash": row[5]
    }


# --------------------------------------------------------------------------
# SESSÕES PERSISTENTES (login sobrevive ao F5 / reload do navegador)
# --------------------------------------------------------------------------

def criar_sessao(usuario_id):
    """Cria uma sessão persistente e retorna o token (a ser guardado na URL)."""

    token = secrets.token_urlsafe(32)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO sessoes(token, usuario_id) VALUES(?, ?)",
        (token, usuario_id),
    )

    conn.commit()
    conn.close()

    return token


def obter_usuario_por_token(token, validade_dias=7):
    """Retorna o usuário de uma sessão válida (não expirada), ou None."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT u.id, u.nome_exibicao, u.funcao, u.tipo, u.email
        FROM sessoes s
        JOIN usuarios u ON u.id = s.usuario_id
        WHERE s.token = ?
          AND s.criado_em >= datetime('now', ?)
        """,
        (token, f"-{validade_dias} days"),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "nome_exibicao": row[1],
        "funcao": row[2] or "",
        "tipo": row[3] or "Paciente",
        "email": row[4],
    }


def remover_sessao(token):
    """Remove a sessão (logout)."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sessoes WHERE token = ?", (token,))

    conn.commit()
    conn.close()


def atualizar_email_usuario(usuario_id, novo_email):
    """Atualiza o email do usuário. Retorna True se ok, False se email já em uso."""

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE usuarios SET email=? WHERE id=?
        """, (novo_email, usuario_id))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def atualizar_funcao_usuario(usuario_id, funcao):
    """Atualiza a função (cargo/papel) do usuário."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("UPDATE usuarios SET funcao=? WHERE id=?", (funcao, usuario_id))

    conn.commit()
    conn.close()


def atualizar_conta_usuario(usuario_id, nome_exibicao, funcao):
    """Atualiza os dados de conta do usuário (nome de exibição e função)."""

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE usuarios SET nome_exibicao=?, funcao=? WHERE id=?",
        (nome_exibicao, funcao, usuario_id),
    )

    conn.commit()
    conn.close()
