"""
Script para importar todos os projetos da planilha Petrobras_Senai_EaD.xlsx
para o banco de dados do ProjectFlow.

Execute DENTRO da pasta project_manager:
    python seed_petrobras.py
"""
import sqlite3, os, unicodedata, pandas as pd
from datetime import datetime

DB_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_manager.db")
EXCEL_SRC = '/mnt/user-data/uploads/Petrobras_-_Senai_EaD.xlsx'
EXCEL_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Petrobras_-_Senai_EaD.xlsx")

BUCKET_STATUS = {
    "PELD":"Ativo","pré-medição":"Ativo",
    "Upload para o BDOC - Files e Scorm":"Ativo",
    "Validação - Desenvolvimento":"Ativo","Autoria digital":"Ativo",
    "Aguardando material base":"Planejamento","Validação - PI":"Ativo",
    "Projetos cancelados/suspensos":"Cancelado","Homologação/Instalação":"Ativo",
    "Desenvolvimento":"Ativo","Projeto Instrucional (PI)":"Ativo",
    "Fazer Cronograma":"Planejamento","Templates e construção de card":"Planejamento",
    "Revisão Textual/Tradução":"Ativo","Aguardando reunião inicial":"Planejamento",
}
PROG_TASK = {"Em andamento":"Em Andamento","Não iniciado":"A Fazer","Concluída":"Concluído"}
PROG_PCT  = {"Em andamento":50.0,"Não iniciado":0.0,"Concluída":100.0}
PRIO_MAP  = {"Urgente":"Crítica","Importante":"Alta","Média":"Média","Baixa":"Baixa"}
CORES = {
    "Angelo Jorge De Almeida Chafin":"#6366f1",
    "Fabiana Cristina Goncalves Ribeiro":"#10b981",
    "Mariana Ribeiro Gonçalves Rodrigues":"#f59e0b",
    "Fatima Satsuki De Araujo Iino":"#8b5cf6",
    "Maria Julia Gouffier":"#ec4899",
    "Thiago Santos De Oliveira":"#06b6d4",
    "Maria Emilia Xavier Pessanha":"#84cc16",
    "Mateus Lima Bastos Peixoto":"#f97316",
    "Simone Bernardo De Castro":"#14b8a6",
    "Daniel David Pereira Da Silva":"#a855f7",
    "Claudio Luis dos Santos Himmelsbach":"#eab308",
    "Debora Alves Pereira":"#ef4444",
    "Tatiana Dias Lutz":"#0ea5e9",
    "Patricia Amorim Pecanha De Souza":"#d946ef",
    "Ana Paula Pedroza Moura":"#64748b",
}
LIDERANCAS = {"Angelo Jorge De Almeida Chafin","Fabiana Cristina Goncalves Ribeiro",
              "Mariana Ribeiro Gonçalves Rodrigues","Fatima Satsuki De Araujo Iino"}

def parse_date(v):
    if v is None: return None
    s = str(v).strip()
    if s in ("","NaN","nan","None","<NA>"): return None
    for fmt in ("%d/%m/%Y","%Y-%m-%d","%d-%m-%Y"):
        try: return datetime.strptime(s,fmt).strftime("%Y-%m-%d %H:%M:%S")
        except: pass
    return None

def slug(name):
    nfkd = unicodedata.normalize('NFKD', name.lower())
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).replace(' ','.')

def hash_pw(pw):
    try:
        import bcrypt
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    except:
        import hashlib, secrets
        salt = secrets.token_hex(16)
        h = hashlib.sha256((salt+pw).encode()).hexdigest()
        return f"sha256${salt}${h}"

def main():
    excel = EXCEL_SRC if os.path.exists(EXCEL_SRC) else EXCEL_LOCAL
    if not os.path.exists(excel):
        print(f"❌ Arquivo Excel não encontrado: {excel}"); return

    print("📊 Lendo planilha...")
    df = pd.read_excel(excel, sheet_name='Tarefas', header=0)
    print(f"   {len(df)} registros")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cur = conn.cursor()

    # Criar tabelas
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL,
        role TEXT DEFAULT 'colaborador', avatar_color TEXT DEFAULT '#6366f1',
        criado_em TEXT);
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
        descricao TEXT, responsavel_id INTEGER, data_inicio TEXT,
        data_fim TEXT, status TEXT DEFAULT 'Planejamento',
        progresso REAL DEFAULT 0.0, criado_em TEXT, atualizado_em TEXT);
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
        descricao TEXT, projeto_id INTEGER, responsavel_id INTEGER,
        status TEXT DEFAULT 'A Fazer', prioridade TEXT DEFAULT 'Média',
        prazo TEXT, data_criacao TEXT, atualizado_em TEXT);
    """)

    # Usuários demo
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for nome,email,senha,role,cor in [
        ("Admin Sistema","admin@demo.com","admin123","admin","#6366f1"),
        ("Maria Gestora","gestor@demo.com","gestor123","gestor","#10b981"),
        ("João Colaborador","colab@demo.com","colab123","colaborador","#f59e0b"),
    ]:
        if not cur.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone():
            cur.execute("INSERT INTO users(nome,email,senha_hash,role,avatar_color,criado_em) VALUES(?,?,?,?,?,?)",
                        (nome,email,hash_pw(senha),role,cor,now))

    # Limpar projetos/tarefas
    cur.execute("DELETE FROM tasks"); cur.execute("DELETE FROM projects")
    conn.commit()

    # Coletar todos os nomes
    nomes = set()
    for col in ['Criado por','Atribuído a','Concluída por']:
        for v in df[col].dropna():
            for p in str(v).split(';'):
                p=p.strip()
                if p and p!='nan': nomes.add(p)

    uid_map = {}
    emails_usados = set(r[0] for r in cur.execute("SELECT email FROM users").fetchall())
    for nome in sorted(nomes):
        row = cur.execute("SELECT id FROM users WHERE nome=?",(nome,)).fetchone()
        if row:
            uid_map[nome]=row[0]; continue
        email_base = f"{slug(nome)[:45]}@petrobras.senai.br"
        email = email_base; n=1
        while email in emails_usados:
            email = f"{slug(nome)[:40]}{n}@petrobras.senai.br"; n+=1
        emails_usados.add(email)
        role = "gestor" if nome in LIDERANCAS else "colaborador"
        cur.execute("INSERT INTO users(nome,email,senha_hash,role,avatar_color,criado_em) VALUES(?,?,?,?,?,?)",
                    (nome,email,hash_pw("senai@2025"),role,CORES.get(nome,"#6366f1"),now))
        uid_map[nome]=cur.lastrowid
    conn.commit()
    print(f"👥 {len(uid_map)} colaboradores criados")

    # Inserir projetos
    proj_ct=0; task_ct=0
    for _,row in df.iterrows():
        nome_proj = str(row.get('Nome da tarefa','')).strip()
        if not nome_proj or nome_proj=='nan': continue

        bucket  = str(row.get('Nome do Bucket','')).strip()
        prog_s  = str(row.get('Progresso','Não iniciado')).strip()
        prio_r  = str(row.get('Prioridade','Média')).strip()
        atr     = str(row.get('Atribuído a','')).strip()
        criador = str(row.get('Criado por','')).strip()
        desc_r  = str(row.get('Descrição','')).strip()
        rotulos = str(row.get('Rótulos','')).strip()
        check   = str(row.get('Itens da lista de verificação','')).strip()
        ic      = str(row.get('Itens concluídos da lista de verificação','')).strip()

        dc = parse_date(row.get('Criado em'))
        di = parse_date(row.get('Data de início'))
        df_= parse_date(row.get('Data de conclusão'))

        st_proj = BUCKET_STATUS.get(bucket,"Ativo")
        pct     = PROG_PCT.get(prog_s,0.0)
        t_st    = PROG_TASK.get(prog_s,"A Fazer")
        if prog_s=="Concluída": st_proj="Concluído"; pct=100.0
        prio = PRIO_MAP.get(prio_r,"Média")

        # Responsável
        pessoas=[]
        if atr and atr!='nan':
            pessoas=[p.strip() for p in atr.split(';') if p.strip() and p.strip()!='nan']
        resp_id = uid_map.get(pessoas[0]) if pessoas else uid_map.get(criador)

        # Descrição
        partes=[]
        if desc_r and desc_r!='nan': partes.append(desc_r.replace('\\n','\n'))
        if rotulos and rotulos!='nan': partes.append(f"Rótulos: {rotulos}")
        if bucket: partes.append(f"Fase: {bucket}")
        desc = "\n\n".join(partes)[:2000]

        cur.execute("""INSERT INTO projects(nome,descricao,responsavel_id,data_inicio,data_fim,
                       status,progresso,criado_em,atualizado_em) VALUES(?,?,?,?,?,?,?,?,?)""",
                    (nome_proj,desc,resp_id,di or dc,df_,st_proj,pct,dc or now,now))
        pid=cur.lastrowid; proj_ct+=1

        # Itens concluídos
        n_conc=0
        if ic and ic!='nan' and '/' in ic:
            try: n_conc=int(ic.split('/')[0].strip())
            except: pass

        if check and check not in ('nan','NaN',''):
            etapas=[e.strip() for e in check.split(';') if e.strip() and e.strip()!='nan']
            for i,etapa in enumerate(etapas):
                prazo_e=None; titulo_e=etapa
                if ' - ' in etapa:
                    p2=etapa.split(' - ',1)
                    dp=p2[0].strip()
                    if len(dp)<=6 and '/' in dp:
                        try:
                            d,m=dp.split('/')
                            ano="2026" if int(m)<=6 else "2025"
                            prazo_e=f"{ano}-{int(m):02d}-{int(d):02d} 00:00:00"
                            titulo_e=p2[1].strip()
                        except: pass
                s_e="Concluído" if (i<n_conc or t_st=="Concluído") else ("Em Andamento" if (t_st=="Em Andamento" and i==n_conc) else "A Fazer")
                rid_e=uid_map.get(pessoas[i%len(pessoas)]) if pessoas else resp_id
                cur.execute("""INSERT INTO tasks(titulo,descricao,projeto_id,responsavel_id,
                               status,prioridade,prazo,data_criacao,atualizado_em) VALUES(?,?,?,?,?,?,?,?,?)""",
                            (titulo_e[:200],f"Etapa: {nome_proj[:100]}",pid,rid_e,s_e,prio,prazo_e or df_,dc or now,now))
                task_ct+=1
        else:
            cur.execute("""INSERT INTO tasks(titulo,descricao,projeto_id,responsavel_id,
                           status,prioridade,prazo,data_criacao,atualizado_em) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (f"Execução: {nome_proj[:180]}",desc[:500],pid,resp_id,t_st,prio,df_,dc or now,now))
            task_ct+=1

        if proj_ct%50==0: conn.commit(); print(f"   ✅ {proj_ct} projetos...")

    conn.commit()
    tp=cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    tt=cur.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    tu=cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()

    print(f"\n{'='*50}")
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print(f"{'='*50}")
    print(f"👥 Usuários:  {tu}")
    print(f"📁 Projetos:  {tp}")
    print(f"✅ Tarefas:   {tt}")
    print(f"{'='*50}")
    print("🔑 admin@demo.com / admin123")
    print("🔑 Colaboradores Petrobras: senha = senai@2025")

if __name__=="__main__":
    main()
