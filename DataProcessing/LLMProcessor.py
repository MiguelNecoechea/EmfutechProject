import requests

class DataAnalyzer:
    """
    This class makes request to the open webui API to analyze data.
    Since the model is Running locally is not possible to actually be practical.
    This class will go through different refactors to access a server using the API.
    But in the cloud
    """
    def __init__(self):
        self.__MODEL = "llama3.2-vision:latest"
        self.__API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjgwNDZkNWYzLWRmMTEtNGMxYi04MWYzLTExZDJhZGY1NTQ3MSJ9.Ylk9uXpAYdCMj7kzjIct5OcrVZ4mRxKduKDOn5xdi-0"
        self._collection_id = None

    @property
    def collection_id(self):
        return self._collection_id

    @collection_id.setter
    def collection_id(self, collection_id):
        self._collection_id = collection_id

    def upload_file(self, file_path):
        url = 'http://localhost:3000/api/v1/files/'
        headers = {
            'Authorization': f'Bearer {self.__API_KEY}',
            'Accept': 'application/json'
        }
        files = {'file': open(file_path, 'rb')}
        response = requests.post(url, headers=headers, files=files)
        response = response.json()
        file_id = response['id']
        return file_id

    def add_file_to_collection(self, file_id):
        if not self._collection_id:
            raise ValueError("Collection ID is not set.")
        url = f'http://localhost:3000/api/v1/knowledge/{self._collection_id}/file/add'
        headers = {
            'Authorization': f'Bearer {self.__API_KEY}',
            'Content-Type': 'application/json'
        }
        data = {'file_id': file_id}
        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def query(self, query):
        if not self._collection_id:
            raise ValueError("Collection ID is not set. The query cannot be executed.")

        url = 'http://localhost:3000/api/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.__API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': self.__MODEL,
            'messages': [{'role': 'user', 'content': query}],
            'files': [{'type': 'collection', 'id': self._collection_id}]
        }
        response = requests.post(url, headers=headers, json=payload)
        response = response.json()
        response = response['choices'][-1]['message']['content']
        return response
