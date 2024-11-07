import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cohere
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Cohere API client
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# Initialize FastAPI app
app = FastAPI()

# Define the input data model for the request
class AssignmentRequest(BaseModel):
    institution_name: str
    name: str
    roll_no: str
    course_name: str
    instructor_name: str
    assignment_topic: str
    heading_no: int
    assignment_len: int
    assignment_format: str

# Helper function to split the word count for each heading
def split_word_count(total_words, heading_no):
    if heading_no <= 0:
        return 0
    return total_words // heading_no

# Endpoint to generate the assignment
@app.post("/generate")
async def generate_assignment(request: AssignmentRequest):
    # Calculate the word count per heading
    heading_word_count = split_word_count(request.assignment_len, request.heading_no)

    # Generate content introduction with student information (this is added only once)
    assignment_content = f"""
    **Institution**: {request.institution_name}\n
    **Student Name**: {request.name}\n
    **Roll Number**: {request.roll_no}\n
    **Course Name**: {request.course_name}\n
    **Instructor**: {request.instructor_name}\n
    **Assignment Topic**: {request.assignment_topic}\n\n
    ---\n
    """

    # Generate content for each heading
    for i in range(1, request.heading_no + 1):
        input_text = f"""
        You are creating an assignment for the topic "{request.assignment_topic}". Here are the details:
        - Heading {i}: Provide unique, detailed content for this section. Make sure to use examples, data, or scenarios to make it informative.
        - Format: {request.assignment_format}
        - Please generate approximately {heading_word_count} words for this heading in a conversational tone.
        """

        try:
            # Call Cohere API to generate content for the current heading
            response = co.generate(
                model='command-xlarge-nightly',
                prompt=input_text,
                max_tokens=heading_word_count * 5,  # Approx. 5 tokens per word
                temperature=0.7,
                frequency_penalty=0.8  # Encourage varied word usage
            )
            
            if response and response.generations:
                # Append the generated content for the current heading
                assignment_content += f"**### Heading {i}:**\n\n" + response.generations[0].text.strip() + "\n\n---\n"
            else:
                raise HTTPException(status_code=500, detail=f"Failed to generate content for heading {i}.")
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating assignment for heading {i}: {str(e)}")

    return {"assignment_content": assignment_content.strip()}
