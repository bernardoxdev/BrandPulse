from pydantic import BaseModel


class IngestaoResponseCLI(BaseModel):
    total: int
    criadas: int
    invalidas: int
    duplicadas: int
