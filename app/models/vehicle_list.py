from datetime import datetime


class VehicleListItem:
    def __init__(
        self,
        nom: str,
        image_url: str,
        created_at: datetime | None = None,
    ):
        self.nom = nom
        self.image_url = image_url
        self.created_at = created_at
