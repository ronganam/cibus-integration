import aiohttp
from aiohttp import ClientSession


class ApiClient:
    def __init__(self, session: ClientSession, username: str, password: str):
        self.base_url = "https://api.capir.pluxee.co.il"
        self.consumer_base_url = "https://api.consumers.pluxee.co.il/api"
        self.headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Application-Id': 'E5D5FEF5-A05E-4C64-AEBA-BA0CECA0E402',
        }
        self.session = session
        self.username = username
        self.password = password
        self.company = ""
        self.user_info = None
        self.budget_info = None

    async def login(self):
        url = f"{self.base_url}/auth/authToken"
        payload = {
            "username": self.username,
            "password": self.password,
            "company": self.company
        }
        try:
            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 201:
                    # Login successful; cookies are automatically handled by the session
                    pass
                else:
                    data = await response.json()
                    error_message = data.get('message', 'Unknown error')
                    raise Exception(f"Login failed: {error_message}")
        except aiohttp.ClientError as e:
            raise Exception(f"An error occurred during login: {e}")

    async def get_user_info(self):
        url = f"{self.consumer_base_url}/prx_user_info.py"
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 401:
                    # Unauthorized; try to re-login
                    await self.login()
                    # Retry the request
                    async with self.session.get(url, headers=self.headers) as retry_response:
                        retry_response.raise_for_status()
                        self.user_info = await retry_response.json()
                else:
                    response.raise_for_status()
                    self.user_info = await response.json()

                if self.user_info.get("http_code") != 200:
                    error_msg = self.user_info.get('msg', 'Unknown error')
                    raise Exception(f"Failed to get user info: {error_msg}")
                return self.user_info
        except aiohttp.ClientError as e:
            raise Exception(f"An error occurred while fetching user info: {e}")

    async def get_budgets(self):
        url = f"{self.consumer_base_url}/main.py"
        payload = {"type": "prx_get_budgets"}
        try:
            async with self.session.post(url, json=payload, headers=self.headers) as response:
                if response.status == 401:
                    # Unauthorized; try to re-login
                    await self.login()
                    # Retry the request
                    async with self.session.post(url, json=payload, headers=self.headers) as retry_response:
                        retry_response.raise_for_status()
                        self.budget_info = await retry_response.json()
                else:
                    response.raise_for_status()
                    self.budget_info = await response.json()

                if self.budget_info.get("http_code") != 200:
                    error_msg = self.budget_info.get('msg', 'Unknown error')
                    raise Exception(f"Failed to get budgets: {error_msg}")
                return self.budget_info
        except aiohttp.ClientError as e:
            raise Exception(f"An error occurred while fetching budgets: {e}")

    @property
    def user_id(self):
        return self.user_info.get('user_id') if self.user_info else None

    @property
    def email(self):
        return self.user_info.get('email') if self.user_info else None

    @property
    def phone(self):
        return self.user_info.get('phone') if self.user_info else None

    @property
    def first_name(self):
        return self.user_info.get('f_name') if self.user_info else None

    @property
    def last_name(self):
        return self.user_info.get('l_name') if self.user_info else None

    @property
    def budget_creation_date(self):
        return self.budget_info.get('data', [{}])[0].get('CreationDate') if self.budget_info else None

    @property
    def budget_expiration_date(self):
        return self.budget_info.get('data', [{}])[0].get('ExpirationDate') if self.budget_info else None

    @property
    def current_budget(self):
        return self.budget_info.get('data', [{}])[0].get('CurrBudget') if self.budget_info else None

    @property
    def creation_budget(self):
        return self.budget_info.get('data', [{}])[0].get('CreatioBudget') if self.budget_info else None
