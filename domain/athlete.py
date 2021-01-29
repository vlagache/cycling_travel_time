class Athlete:

    def __init__(self, id_: int, refresh_token: str, access_token: str,
                 token_expires_at: int, firstname: str, lastname: str):
        self.id = id_
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.token_expires_at = token_expires_at
        self.firstname = firstname
        self.lastname = lastname


class AthleteRepository:

    def get(self, id_) -> Athlete:
        raise NotImplementedError()

    def save(self, athlete: Athlete):
        raise NotImplementedError()

    def update_tokens(self, id_, access_token, refresh_token, token_expires_at):
        raise NotImplementedError()

    def search_if_exist(self, firstname, lastname) -> Athlete:
        raise NotImplementedError()


repository: AthleteRepository
