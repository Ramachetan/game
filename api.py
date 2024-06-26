from fastapi import FastAPI, HTTPException
from typing import Dict
import pandas as pd
from ast import literal_eval
import vertexai
from app import game
from stats import aggregate_statistics
# from chat import get_response_from_model
from vertexai.preview.generative_models import GenerativeModel
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ast import literal_eval

app = FastAPI()

origins = [
    "http://localhost:5173",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Player(BaseModel):
    player_id: str
    
class ChatMessage(BaseModel):
    message: str
    player_id: str
    
import logging

logging.basicConfig(level=logging.INFO)


@app.post("/generate_summary/")
async def generate_summary_endpoint(player: Player) -> Dict:
    player_id = str(player.player_id)
    try:
        # Initialize Vertex AI
        vertexai.init(project="fresh-span-400217", location="us-central1") 
        model = GenerativeModel("gemini-1.0-pro-001")
        
        logging.info(f"Calling game function with player_id: {player_id}")
        game(player_id)
        
        # Load data
        logging.info(f"Loading CSV file for player_id: {player_id}")
        df = pd.read_csv(f'telematics/{player_id}_vehicle_data.csv')

        logging.info("Aggregating statistics")
        summary = aggregate_statistics(df)

        # Generate content
        logging.info("Generating content")
        responses = model.generate_content(
            f"""{summary}\n\n Above are the statistics for the vehicle with player_id: {player_id}, Generate a user-friendly summary and insights from the vehicle performance statistics obtained from a BeamNG.drive simulation driven by the player. The data reflects various performance metrics recorded on an automation test track. Given the statistics, provide insights and recommendations for the player to improve their driving skills and vehicle performance. The user-friendly summary should be in a conversational format and should be easy to understand for the player. Round off the numbers to 2 decimal places use imperial units\n""",
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0,
                "top_p": 1
            },
            stream=False,
        )
        
        fuel_data = [{'Time': row['Time'], 'Fuel Level': row['fuel']} for index, row in df.iterrows()]
        oil_temp_data = [{'Time': row['Time'], 'Oil Temperature': row['oil_temperature']} for index, row in df.iterrows()]
        water_temp_data = [{'Time': row['Time'], 'Water Temperature': row['water_temperature']} for index, row in df.iterrows()]
        gear_distribution = df['gear'].value_counts().reset_index().rename(columns={'index': 'Gear', 'gear': 'Frequency'})
        gear_distribution_data = [{'Gear': row['Gear'], 'Frequency': row['Frequency']} for index, row in gear_distribution.iterrows()]
        part_damage = literal_eval(df['part_damage'].iloc[-1])
        steering = df['steering'].diff().abs().sum()
        graphs = [
            {
                'graph_type': 'pie',
                'title': 'Damaged Parts Distribution',
                'data': part_damage
            },
            {
                'graph_type': 'bar',
                'title': 'Gear Distribution',
                'x_axis': 'Gear',
                'y_axis': 'Frequency',
                'data': gear_distribution_data
            },
            {
                'graph_type': 'line',
                'title': 'Fuel Level Over Time',
                'x_axis': 'Time',
                'y_axis': 'Fuel Level',
                'data': fuel_data
            },
            {
                'graph_type': 'line',
                'title': 'Oil Temperature Over Time',
                'x_axis': 'Time',
                'y_axis': 'Oil Temperature',
                'data': oil_temp_data
            },
            {
                'graph_type': 'line',
                'title': 'Water Temperature Over Time',
                'x_axis': 'Time',
                'y_axis': 'Water Temperature',
                'data': water_temp_data
            },
            {
                'graph_type': 'area',
                'title': 'Steering Changes',
                'x_axis': 'Time',
                'y_axis': 'Steering',
                'data': [{'Time': row['Time'], 'Steering': row['steering']} for index, row in df.iterrows()]
            }
        ]
        
        df = pd.read_csv(f'telematics/{player.player_id}_vehicle_data.csv')
        dtc_codes = df['DTC'].iloc[0]
    
        model = GenerativeModel("gemini-1.0-pro-001")
        dtc_response = model.generate_content(
            f"""{dtc_codes}\n\nBased on the above DTC codes, What could be the root cause of the problem? Also, provide the diagnostic steps and recommended fixes for the problem. Generate a detailed report. The report will identify potential root causes, provide a step-by-step diagnostic approach, and recommend solutions to resolve the issues.""",
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0,
                "top_p": 1
            },
            stream=False,
        )
    
   

        return {"generated_text": responses.text, "player_id": player_id, "graphs": graphs, "dtc_response": dtc_response.text, "dtc_codes": dtc_codes}
    
    

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
def multiturn_generate_content(chat_message: ChatMessage):
    message = chat_message.message
    player_id = chat_message.player_id
    message = chat_message.message
    model = GenerativeModel("gemini-1.0-pro-001")
    model = GenerativeModel(
    "gemini-1.0-pro-001",
    )
    chat = model.start_chat()
    chat.send_message(
      ["""DTC codes are [\'P0550\', \'P0331\', \'P0467\', \'P0456\', \'P0328\']"""],)
    chat.send_message(
      ["""Based on the above DTC codes, What could be the root cause of the problem? Also, provide the diagnostic steps and recommended fixes for the problem. Generate a detailed report. The report will identify potential root causes, provide a step-by-step diagnostic approach, and recommend solutions to resolve the issues."""])
    chat.send_message(
        [""" Potential Root Causes: The provided DTC codes indicate potential issues with the vehicle's emissions control system, specifically: P0550: Intake Air Heater Control Circuit Malfunction P0331: Knock Sensor 1 Circuit Range/Performance P0467: Evaporative Emission Control System Purge Control Valve Circuit P0456: Evaporative Emission Control System Small Leak Detected P0328: Knock Sensor 2 Circuit High Input These codes suggest that there may be problems with the vehicle's air/fuel mixture, ignition timing, or evaporative emissions system. Diagnostic Steps: Read and Clear DTCs: Use a diagnostic scanner to read and clear the stored DTCs. This will provide a baseline for further diagnosis. Inspect Intake Air Heater: Check the intake air heater for any damage or loose connections. Ensure that the heater is receiving power and ground. Test Knock Sensors: Use an oscilloscope or multimeter to test the knock sensors for proper signal output. Check for any loose connections or damaged wiring. Inspect Purge Control Valve: Locate the purge control valve and check for any leaks or damage. Ensure that the valve is receiving power and ground. Check Evaporative Emissions System: Perform a smoke test or pressure test to identify any leaks in the evaporative emissions system. Inspect the fuel tank, fuel lines, and other components for damage. Recommended Fixes: Based on the diagnostic results, the following repairs may be necessary: Replace Intake Air Heater: If the intake air heater is damaged or not receiving power, it should be replaced. Replace Knock Sensor: If the knock sensor is faulty or has a damaged wiring harness, it should be replaced. Clean or Replace Purge Control Valve: If the purge control valve is leaking or not receiving power, it should be cleaned or replaced. Repair Evaporative Emissions System Leak: Identify and repair any leaks in the evaporative emissions system, such as damaged fuel lines or a faulty fuel tank. Reset Engine Control Module (ECM): After completing the repairs, reset the ECM to clear any remaining DTCs and allow the system to relearn its parameters. Additional Notes: It is important to address these issues promptly to prevent further damage to the vehicle's emissions control system. If the diagnostic steps or repairs are beyond your technical ability, it is recommended to consult a qualified mechanic. Regular maintenance, such as spark plug replacement and air filter cleaning, can help prevent these types of issues from occurring.
         """]
    )
    response = chat.send_message(
        message,
        generation_config={
            "max_output_tokens": 2048,
            "temperature": 0,
            "top_p": 1
        },
        stream=False,
    )
    return {"response": response.text}

    

# To run the server, execute the following command: uvicorn api:app --reload