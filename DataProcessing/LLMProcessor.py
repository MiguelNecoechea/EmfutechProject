import os
import csv
import pandas as pd


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
        # OpenAI.api_key = self.__API_KEY
        self._files_id = []
        # self.client = OpenAI()

    # def upload_file(self, file_path, purpose="assistants"):
    #     """
    #     Upload a CSV file to the OpenAI API.
    #
    #     Args:
    #         file_path (str): The path to the CSV file to upload.
    #         purpose (str): The purpose of the file upload (default: "data_analysis").
    #
    #     Returns:
    #         str: The file ID from the API response.
    #     """
    #
    #     # Convert CSV to TXT
    #     txt_path = file_path.rsplit('.', 1)[0] + '.txt'
    #     with open(file_path, 'r') as csv_file, open(txt_path, 'w') as txt_file:
    #         csv_reader = csv.reader(csv_file)
    #         for row in csv_reader:
    #             txt_file.write('\t'.join(row) + '\n')
    #
    #     # Upload TXT file
    #     file = self.client.files.create(
    #         file=open(txt_path, "rb"),
    #         purpose=purpose
    #     )
    #     self._files_id.append(file.id)
    #
    #     # Clean up temporary txt file
    #     os.remove(txt_path)
    #
    # def query(self, prompt, temperature=0.2):
    #     """
    #     Sends a prompt along with the uploaded file to the OpenAI API and retrieves the response.
    #
    #     Args:
    #         prompt (str): The prompt to send to the model.
    #         temperature (float): Sampling temperature.
    #
    #     Returns:
    #         str: The model's response.
    #     """
    #     try:
    #         model = self.client.beta.assistants.create(
    #             model=self.__MODEL,
    #             instructions="You are a data explainer bot. You are given a csv file and a prompt. You need to explain the data in the csv file according to the prompt. Following the rules carefully. The user cannot interact with you, so you must not ask follow up questions.",
    #             name="Data explainer bot",
    #             tools=[{"type": "file_search"}]
    #         )
    #
    #         thread = self.client.beta.threads.create()
    #
    #         thread_message = self.client.beta.threads.messages.create(
    #             thread_id=thread.id,
    #             role="user",
    #             content=prompt,
    #             attachments=[{"file_id": file_id, "tools": [{"type": "file_search"}]} for file_id in self._files_id]
    #         )
    #
    #         run = self.client.beta.threads.runs.create(
    #             thread_id=thread.id,
    #             assistant_id=model.id
    #         )
    #
    #         # Add timeout and proper status checking
    #         import time
    #         timeout = 300  # 5 minutes timeout
    #         start_time = time.time()
    #
    #         while True:
    #             run = self.client.beta.threads.runs.retrieve(
    #                 thread_id=thread.id,
    #                 run_id=run.id
    #             )
    #
    #             if run.status == "completed":
    #                 messages = self.client.beta.threads.messages.list(
    #                     thread_id=thread.id
    #                 )
    #                 # Get the last assistant message
    #                 for message in messages:
    #                     if message.role == "assistant":
    #                         return message.content[0].text.value
    #
    #             elif run.status == "failed":
    #                 raise Exception("Run failed with error: " + str(run.last_error))
    #
    #             elif time.time() - start_time > timeout:
    #                 raise TimeoutError("Request timed out after 5 minutes")
    #
    #             time.sleep(1)  # Wait 1 second before checking again
    #     finally:
    #         # Cleanup resources
    #         if 'model' in locals():
    #             self.client.beta.assistants.delete(model.id)
    #         if 'thread' in locals():
    #             self.client.beta.threads.delete(thread.id)
    #
    # def cleanup_files(self):
    #     """Clean up all uploaded files."""
    #     for file_id in self._files_id:
    #         self.client.files.delete(file_id)
    #     self._files_id.clear()
    
    def preprocess_aura(self, file_path, training_file_path):
        """Preprocess the AURA file by normalizing beta columns using training data averages."""
        
        # Read the main file into pandas DataFrame
        df = pd.read_csv(file_path, sep=',')
        
        # Get timestamp column
        timestamp = df['timestamp']
        
        # Filter columns that contain 'beta' (case insensitive)
        beta_columns = [col for col in df.columns if 'beta' in col.lower()]
        df_beta = df[beta_columns]

        # Calculate averages for each 100 rows (approximately 1 second of data)
        chunk_size = 100
        chunks = [df_beta[i:i + chunk_size] for i in range(0, len(df_beta), chunk_size)]
        timestamp_chunks = [timestamp[i:i + chunk_size] for i in range(0, len(timestamp), chunk_size)]
        
        # Calculate mean for each chunk
        df_beta = pd.DataFrame([chunk.mean() for chunk in chunks], columns=beta_columns)
        timestamp = pd.Series([chunk.mean() for chunk in timestamp_chunks])

        try:
            # Try to read and process training data if it exists
            df_training = pd.read_csv(training_file_path, sep=',')
            beta_columns_training = [col for col in df_training.columns if 'beta' in col.lower()]
            df_beta_training = df_training[beta_columns_training]
            
            # Calculate averages from training data
            training_averages = df_beta_training.mean()
            
            # Normalize beta columns using training averages
            for col in beta_columns:
                if col in beta_columns_training:
                    df_beta[col] = df_beta[col] / training_averages[col]
            
            df_beta = df_beta.round(3)
            timestamp = timestamp.round(3)
            training_exists = True
            
        except (FileNotFoundError, pd.errors.EmptyDataError):
            # Just process in chunks if no training data exists
            df_beta = df_beta.round(3)
            timestamp = timestamp.round(3)
            training_exists = False
        
        # Save processed data
        pd.concat([timestamp, df_beta], axis=1).to_csv(file_path, sep=',', index=False)
        return df_beta, training_exists
