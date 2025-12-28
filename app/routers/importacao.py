from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session
from typing import List
import pandas as pd
from io import BytesIO

from app.database import get_session
from app.models import Transacao, TransacaoRead
from app.services.regras import aplicar_todas_regras_ativas

router = APIRouter(prefix="/importacao", tags=["Importação"])


@router.post("/extrato", response_model=List[TransacaoRead])
async def importar_extrato(
    arquivo: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Importa transações de um arquivo de extrato bancário (CSV ou Excel)
    
    Formato esperado:
    - data: formato DD/MM/YYYY ou YYYY-MM-DD (obrigatório)
    - descricao: texto descritivo (obrigatório)
    - valor: número (positivo para entradas, negativo para saídas) (obrigatório)
    - categoria: texto (opcional)
    """
    if not arquivo.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Formato de arquivo não suportado. Use CSV ou Excel."
        )
    
    conteudo = await arquivo.read()
    
    try:
        if arquivo.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(conteudo))
        else:
            df = pd.read_excel(BytesIO(conteudo))
        
        # Normaliza os nomes das colunas
        df.columns = df.columns.str.lower().str.strip()
        
        # Validações básicas
        colunas_requeridas = ['data', 'descricao', 'valor']
        for col in colunas_requeridas:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Coluna '{col}' não encontrada no arquivo"
                )
        
        transacoes_criadas = []
        
        for _, row in df.iterrows():
            # Converte a data
            if isinstance(row['data'], str):
                if '/' in row['data']:
                    data = pd.to_datetime(row['data'], format='%d/%m/%Y').date()
                else:
                    data = pd.to_datetime(row['data']).date()
            else:
                data = pd.to_datetime(row['data']).date()
            
            valor = float(row['valor'])
            
            # Determina o tipo baseado no valor
            tipo = "entrada" if valor > 0 else "saida"
            valor_abs = abs(valor)
            
            # Pega categoria se existir no arquivo
            categoria = row.get('categoria', None)
            
            transacao = Transacao(
                data=data,
                descricao=str(row['descricao']),
                valor=valor_abs,
                valor_original=valor_abs,  # Define valor original na importação
                tipo=tipo,
                categoria=categoria,
                origem="extrato_bancario"
            )
            
            session.add(transacao)
            transacoes_criadas.append(transacao)
        
        session.commit()
        
        # Aplicar regras ativas em cada transação importada de extrato
        for t in transacoes_criadas:
            session.refresh(t)
            aplicar_todas_regras_ativas(t, session)
        
        # Commit final após aplicar regras
        session.commit()
        
        # Refresh final para obter estado atualizado
        for t in transacoes_criadas:
            session.refresh(t)
        
        return transacoes_criadas
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.post("/fatura", response_model=List[TransacaoRead])
async def importar_fatura(
    arquivo: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Importa transações de uma fatura de cartão de crédito (CSV ou Excel)
    
    Formato esperado:
    - data: formato DD/MM/YYYY ou YYYY-MM-DD (obrigatório)
    - descricao: texto descritivo (obrigatório)
    - valor: número (sempre positivo, representa saída) (obrigatório)
    - categoria: texto (opcional)
    - data_fatura: formato DD/MM/YYYY ou YYYY-MM-DD (opcional, data de fechamento/pagamento)
    """
    if not arquivo.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Formato de arquivo não suportado. Use CSV ou Excel."
        )
    
    conteudo = await arquivo.read()
    
    try:
        if arquivo.filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(conteudo))
        else:
            df = pd.read_excel(BytesIO(conteudo))
        
        # Normaliza os nomes das colunas
        df.columns = df.columns.str.lower().str.strip()
        
        # Validações básicas
        colunas_requeridas = ['data', 'descricao', 'valor']
        for col in colunas_requeridas:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Coluna '{col}' não encontrada no arquivo"
                )
        
        transacoes_criadas = []
        
        for _, row in df.iterrows():
            # Converte a data
            if isinstance(row['data'], str):
                if '/' in row['data']:
                    data = pd.to_datetime(row['data'], format='%d/%m/%Y').date()
                else:
                    data = pd.to_datetime(row['data']).date()
            else:
                data = pd.to_datetime(row['data']).date()
            
            valor = abs(float(row['valor']))  # Sempre positivo
            
            # Pega categoria se existir no arquivo
            categoria = row.get('categoria', None)
            
            # Pega data_fatura se existir no arquivo
            data_fatura = None
            if 'data_fatura' in row and pd.notna(row['data_fatura']):
                if isinstance(row['data_fatura'], str):
                    if '/' in row['data_fatura']:
                        data_fatura = pd.to_datetime(row['data_fatura'], format='%d/%m/%Y').date()
                    else:
                        data_fatura = pd.to_datetime(row['data_fatura']).date()
                else:
                    data_fatura = pd.to_datetime(row['data_fatura']).date()
            
            transacao = Transacao(
                data=data,
                descricao=str(row['descricao']),
                valor=valor,
                valor_original=valor,  # Define valor original na importação
                tipo="saida",  # Fatura sempre é saída
                categoria=categoria,
                origem="fatura_cartao",
                data_fatura=data_fatura
            )
            
            session.add(transacao)
            transacoes_criadas.append(transacao)
        
        session.commit()
        
        # Aplicar regras ativas em cada transação importada de fatura
        for t in transacoes_criadas:
            session.refresh(t)
            aplicar_todas_regras_ativas(t, session)
        
        # Commit final após aplicar regras
        session.commit()
        
        # Refresh final para obter estado atualizado
        for t in transacoes_criadas:
            session.refresh(t)
        
        return transacoes_criadas
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )
