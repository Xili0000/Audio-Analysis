# Cloud Shell MP3 Processing Tool

This is an automation tool designed to connect to Google Cloud Shell, upload MP3 files, process audio using Python scripts in Cloud Shell, and then download the generated files.

## Features

- Automatically obtains Google Cloud Shell connection information
- Automatically connects to the Cloud Shell environment
- Uploads MP3 files to Cloud Shell
- Executes specified Python scripts in Cloud Shell
- Automatically downloads generated files 

## Requirements

1. Python 3.6+
2. Google Cloud SDK (gcloud command-line tool)
3. The following Python library:
   ```
   pip install paramiko
   ```

## Preparation

1. Ensure Google Cloud SDK is installed and configured
2. Make sure Google Cloud Shell service is enabled
3. Have the Python script for MP3 processing ready in your Cloud Shell

## Usage

```bash
python dynamic_cloud_shell.py <Python_file_in_Cloud_Shell> <mp3_file_path>
```

### Parameters

- `<Python_file_in_Cloud_Shell>`: Your Python script in Cloud Shell that processes MP3 files
- `<mp3_file_path>`: Local path to the MP3 file you want to process

### Example

```bash
python dynamic_cloud_shell.py mp3totext.py example.mp3
```

## Workflow

1. The script automatically connects to your Google Cloud Shell
2. Uploads the specified MP3 file to Cloud Shell
3. Executes the specified Python script in Cloud Shell to process the MP3 file
4. Downloads the resulting files (responses_output.txt and converted_audio.wav) to your local directory

## Notes

- Make sure you have the appropriate Python script in your Cloud Shell for processing MP3 files
- You may need to install the gcloud alpha component when running for the first time
- If the connection fails, the script will attempt to start Cloud Shell and reconnect 
