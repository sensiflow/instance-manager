import psycopg


class DataSource:

    def __init__(self, db_url: str):
        self.db_url = db_url

    def get_connection(self):
        return psycopg.connect(self.db_url)
