from domain.athlete import Athlete


class AdapterAthlete:

    def __init__(self, data: dict):
        self.data = data

    def id(self) -> int:
        return self.data.get("athlete").get("id")

    def refresh_token(self) -> str:
        return self.data.get("refresh_token")

    def access_token(self) -> str:
        return self.data.get("access_token")

    def token_expires_at(self) -> int:
        return self.data.get("expires_at")

    def firstname(self) -> str:
        return self.data.get("athlete").get("firstname")

    def lastname(self) -> str:
        return self.data.get("athlete").get("lastname")

    def get(self) -> Athlete:
        return Athlete(
            id_=self.id(),
            refresh_token=self.refresh_token(),
            access_token=self.access_token(),
            token_expires_at=self.token_expires_at(),
            firstname=self.firstname(),
            lastname=self.lastname()
        )
