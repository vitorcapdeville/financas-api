"""
Exceções da camada de aplicação
"""


class ApplicationException(Exception):
    """Exceção base da aplicação"""
    pass


class EntityNotFoundException(ApplicationException):
    """Entidade não encontrada"""
    def __init__(self, entity_name: str, entity_id: any):
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id {entity_id} not found")


class DuplicateEntityException(ApplicationException):
    """Entidade duplicada"""
    def __init__(self, entity_name: str, field: str, value: any):
        self.entity_name = entity_name
        self.field = field
        self.value = value
        super().__init__(f"{entity_name} with {field}='{value}' already exists")


class ValidationException(ApplicationException):
    """Erro de validação de dados"""
    pass


class BusinessRuleException(ApplicationException):
    """Violação de regra de negócio"""
    pass
