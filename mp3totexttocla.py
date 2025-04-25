import os
import sys
from pydub import AudioSegment
from google.cloud import speech
from google.cloud import storage
import nltk
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
from googleapiclient import discovery
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "thermal-origin-454105-s5-c6291f413f44.json"
API_KEY = 'AIzaSyDGwQzJDQe_lJv7YnhnM3JFjQDA0HRZUf8'

# The following two lines are only needed the first time to download NLTK data. Comment them out after downloading.
#nltk.download('punkt')
#nltk.download('punkt_tab')

def transcribe_mp3_to_text(mp3_path, bucket_name, language_code):
    wav_path = "converted_audio.wav"
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(wav_path, format="wav")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    destination_blob_name = "converted_audio.wav"
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(wav_path)

    client = speech.SpeechClient()

    audio_gcs = speech.RecognitionAudio(uri=f"gs://{bucket_name}/{destination_blob_name}")
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
        alternative_language_codes=["zh-CN", "fr-FR", "ja-JP", "ru-RU", "ar-SA"],
        enable_automatic_punctuation=True
    )

    operation = client.long_running_recognize(config=config, audio=audio_gcs)
    response = operation.result(timeout=300)

    transcriptions = []
    language = None
    for result in response.results:
        transcript = result.alternatives[0].transcript
        language = result.language_code
        transcriptions.append(transcript)

    combined_transcription = " ".join(transcriptions)
    return f"{language}\n{combined_transcription}"

def split_into_sentences(text):
    sentences = nltk.sent_tokenize(text)
    return sentences

def ask_question(text: str):
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    safety_settings = [
        SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                     threshold=SafetySetting.HarmBlockThreshold.OFF),
        SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                     threshold=SafetySetting.HarmBlockThreshold.OFF),
        SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                     threshold=SafetySetting.HarmBlockThreshold.OFF),
        SafetySetting(category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                     threshold=SafetySetting.HarmBlockThreshold.OFF),
    ]

    vertexai.init(
        project="829020429280",
        location="us-central1",
        api_endpoint="us-central1-aiplatform.googleapis.com"
    )

    model = GenerativeModel(
        "projects/829020429280/locations/us-central1/endpoints/6002987141494210560",
    )

    chat = model.start_chat()
    response = chat.send_message(
        text,
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    return response.text

def analyze_toxicity(text):
    client = discovery.build(
        "commentanalyzer",
        "v1alpha1",
        developerKey=API_KEY,
        discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
        static_discovery=False,
    )

    analyze_request = {
        'comment': {'text': text},
        'requestedAttributes': {
            'TOXICITY': {},
            'SEVERE_TOXICITY': {},
            'INSULT': {},
            'PROFANITY': {},
            'THREAT': {},
            'IDENTITY_ATTACK': {}
        }
    }

    try:
        response = client.comments().analyze(body=analyze_request).execute()
        return response["attributeScores"]
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return None

def process_and_ask(mp3_path):
    transcribed_text = transcribe(mp3_path)
    transcription_content = transcribed_text.split("\n")[1]
    sentences = split_into_sentences(transcription_content)

    # Analyze toxicity of the full text
    full_text_toxicity = analyze_toxicity(transcription_content)
    
    prompt_text = "\n\nPlease determine whether this sentence is toxic; if it is, output 'toxic', if it is not, output 'non-toxic':\n\n"
    responses = []
    is_toxic = False
    output_text = []

    # Add overall toxicity analysis result
    if full_text_toxicity:
        output_text.append("Overall toxicity analysis of the full text:")
        for attr, score_obj in full_text_toxicity.items():
            score = score_obj["summaryScore"]["value"]
            output_text.append(f"{attr}: {score:.4f}")
        output_text.append("\n")

    # Analyze each sentence
    for i, sentence in enumerate(sentences, 1):
        question_text = sentence + prompt_text
        response = ask_question(question_text)
        sentence_toxicity = analyze_toxicity(sentence)

        if not response or response.strip() == "":
            continue

        response = response.strip()
        response_dict = {
            "sentence": sentence,
            "response": response,
            "toxicity_scores": sentence_toxicity
        }
        responses.append(response_dict)

        if response.lower() == 'toxic':
            is_toxic = True

        output_text.append(f"Sentence {i}: {sentence}")
        output_text.append(f"AI Judgment {i}: {response}")
        
        if sentence_toxicity:
            output_text.append(f"Toxicity Analysis {i}:")
            for attr, score_obj in sentence_toxicity.items():
                score = score_obj["summaryScore"]["value"]
                output_text.append(f"  {attr}: {score:.4f}")
        output_text.append("\n")

    overall_response = "toxic" if is_toxic else "non-toxic"
    transcription_lan = transcribed_text.split("\n")[0]
    print(f"Language: {transcription_lan}")
    print(f"Final Result: {overall_response}")

    with open("toxicity_analysis_output.txt", "w", encoding="utf-8") as file:
        file.write("\n".join(output_text))
        file.write(f"\nFinal Result: {overall_response}")

def transcribe(mp3_path, bucket_name="my-speech-bucket1ze", language_code="en-US"):
    return transcribe_mp3_to_text(mp3_path, bucket_name, language_code)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python newtest.py <path_to_mp3_file>")
        sys.exit(1)
        
    mp3_path = sys.argv[1]
    if not os.path.exists(mp3_path):
        print(f"Error: File {mp3_path} does not exist")
        sys.exit(1)
        
    process_and_ask(mp3_path)