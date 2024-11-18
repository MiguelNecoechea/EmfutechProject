from openai import OpenAI
import os
import requests
import csv
from datetime import datetime
import time

class DataAnalyzer:
    """
    This class interfaces with the OpenAI API to analyze CSV data.
    It handles uploading files, managing collections, and querying the model for analysis.
    """

    def __init__(self):
        self.__MODEL = "gpt-4o-mini" 
        self.__API_KEY = os.getenv("OPENAI_API_KEY")
        if not self.__API_KEY:
            raise ValueError("OpenAI API key not set in the environment variables.")
        OpenAI.api_key = self.__API_KEY
        self._files_id = []
        self.client = OpenAI()

    def upload_file(self, file_path, purpose="assistants"):
        """
        Upload a CSV file to the OpenAI API.

        Args:
            file_path (str): The path to the CSV file to upload.
            purpose (str): The purpose of the file upload (default: "data_analysis").

        Returns:
            str: The file ID from the API response.
        """
        
        # Convert CSV to TXT
        txt_path = file_path.rsplit('.', 1)[0] + '.txt'
        with open(file_path, 'r') as csv_file, open(txt_path, 'w') as txt_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                txt_file.write('\t'.join(row) + '\n')
                
        # Upload TXT file
        file = self.client.files.create(
            file=open(txt_path, "rb"),
            purpose=purpose
        )
        self._files_id.append(file.id)
        
        # Clean up temporary txt file
        os.remove(txt_path)

    def query(self, prompt, temperature=0.2):
        """
        Sends a prompt along with the uploaded file to the OpenAI API and retrieves the response.

        Args:
            prompt (str): The prompt to send to the model.
            temperature (float): Sampling temperature.

        Returns:
            str: The model's response.
        """
        try:
            model = self.client.beta.assistants.create(
                model=self.__MODEL,
                instructions="You are a data explainer bot. You are given a csv file and a prompt. You need to explain the data in the csv file according to the prompt. Following the rules carefully. The user cannot interact with you, so you must not ask follow up questions.",
                name="Data explainer bot",
                tools=[{"type": "file_search"}]
            )

            thread = self.client.beta.threads.create()

            thread_message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt,
                attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in self._files_id]
            )

            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=model.id
            )

            # Add timeout and proper status checking
            import time
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            
            while True:
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                
                if run.status == "completed":
                    messages = self.client.beta.threads.messages.list(
                        thread_id=thread.id
                    )
                    # Get the last assistant message
                    for message in messages:
                        if message.role == "assistant":
                            return message.content[0].text.value
                    
                elif run.status == "failed":
                    raise Exception("Run failed with error: " + str(run.last_error))
                
                elif time.time() - start_time > timeout:
                    raise TimeoutError("Request timed out after 5 minutes")
                
                time.sleep(1)  # Wait 1 second before checking again  
        finally:
            # Cleanup resources
            if 'model' in locals():
                self.client.beta.assistants.delete(model.id)
            if 'thread' in locals():
                self.client.beta.threads.delete(thread.id)

    def cleanup_files(self):
        """Clean up all uploaded files."""
        for file_id in self._files_id:
            self.client.files.delete(file_id)
        self._files_id.clear()
