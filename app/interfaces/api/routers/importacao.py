"""
Router refatorado para Importação usando Clean Architecture
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

from app.application.use_cases.importar_extrato import ImportarExtratoUseCase
from app.application.use_cases.importar_fatura import ImportarFaturaUseCase
from app.application.exceptions import ValidationException
from app.interfaces.api.schemas.request_response import ResultadoImportacaoResponse
from app.interfaces.api.dependencies import (
    get_importar_extrato_use_case,
    get_importar_fatura_use_case
)


router = APIRouter(
    prefix="/importacao",
    tags=["Importação"]
)


@router.post("/extrato", response_model=ResultadoImportacaoResponse)
async def importar_extrato(
    arquivo: UploadFile = File(...),
    use_case: ImportarExtratoUseCase = Depends(get_importar_extrato_use_case)
):
    """
    Importa transações de um arquivo de extrato bancário (CSV ou Excel).
    
    Formato esperado:
    - data: formato DD/MM/YYYY ou YYYY-MM-DD (obrigatório)
    - descricao: texto descritivo (obrigatório)
    - valor: número (positivo para entradas, negativo para saídas) (obrigatório)
    - categoria: texto (opcional)
    
    Processamento automático:
    - Tag "Rotina" é adicionada a todas as transações
    - Regras ativas são aplicadas automaticamente
    
    Args:
        arquivo: Arquivo CSV ou Excel com as transações
        
    Returns:
        Resultado da importação com total e IDs das transações criadas
        
    Raises:
        400: Formato de arquivo inválido ou dados incorretos
        500: Erro no processamento
    """
    try:
        # Ler conteúdo do arquivo
        conteudo = await arquivo.read()
        
        # Executar caso de uso
        resultado = use_case.execute(
            arquivo=conteudo,
            nome_arquivo=arquivo.filename or ""
        )
        
        return ResultadoImportacaoResponse(
            total_importado=resultado.total_importado,
            transacoes_ids=resultado.transacoes_ids,
            mensagem=resultado.mensagem
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )


@router.post("/fatura", response_model=ResultadoImportacaoResponse)
async def importar_fatura(
    arquivo: UploadFile = File(...),
    use_case: ImportarFaturaUseCase = Depends(get_importar_fatura_use_case)
):
    """
    Importa transações de uma fatura de cartão de crédito (CSV ou Excel).
    
    Formato esperado:
    - data: formato DD/MM/YYYY ou YYYY-MM-DD (obrigatório)
    - descricao: texto descritivo (obrigatório)
    - valor: número (sempre positivo, representa saída) (obrigatório)
    - categoria: texto (opcional)
    - data_fatura: formato DD/MM/YYYY ou YYYY-MM-DD (opcional, data de fechamento/pagamento)
    
    Processamento automático:
    - Todas as transações são criadas como "saída"
    - Valores são convertidos para positivos automaticamente
    - Tag "Rotina" é adicionada a todas as transações
    - Regras ativas são aplicadas automaticamente
    
    Args:
        arquivo: Arquivo CSV ou Excel com as transações
        
    Returns:
        Resultado da importação com total e IDs das transações criadas
        
    Raises:
        400: Formato de arquivo inválido ou dados incorretos
        500: Erro no processamento
    """
    try:
        # Ler conteúdo do arquivo
        conteudo = await arquivo.read()
        
        # Executar caso de uso
        resultado = use_case.execute(
            arquivo=conteudo,
            nome_arquivo=arquivo.filename or ""
        )
        
        return ResultadoImportacaoResponse(
            total_importado=resultado.total_importado,
            transacoes_ids=resultado.transacoes_ids,
            mensagem=resultado.mensagem
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )
