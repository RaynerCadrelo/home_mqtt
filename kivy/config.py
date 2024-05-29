from pydantic import BaseModel

class Setting(BaseModel):
    host: str = ""
    topic_turbina: str = ""
    topic_turbina_action: str = ""
    time_is_connected: int =  5  # Tiempo para considerarse que se está conectado
