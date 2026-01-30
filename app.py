import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import sys  # Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.connection import get_connection
from db.create_db import create_tables
from face_embeddings import FaceEmbedder

app = FastAPI(title="User Registration System", version="1.0.0")

# Create necessary directories
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")    
templates = Jinja2Templates(directory="templates")

# Initialize database and embedder
create_tables()
embedder = FaceEmbedder()

# Pydantic models for request validation
class UserCreate(BaseModel):
    user_id: str
    username: str
    department: str
    designation: str

class PhotoData(BaseModel):
    angle: str
    image_data: str  # base64 encoded image

class UserRegistration(BaseModel):
    user: UserCreate
    photos: List[PhotoData]

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main registration page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/users")
async def get_users():
    """Get all registered users from database"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username, department, designation, registration_date FROM users")
            users = cur.fetchall()
        return JSONResponse(content={"users": users})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        conn.close()

@app.post("/api/users/register")
async def register_user(registration: UserRegistration):
    """Register a new user with photos and generate concatenated embeddings"""
    try:
        user_data = registration.user
        photos_data = registration.photos
        # Validate user data
        if not all([user_data.user_id, user_data.username, 
                user_data.department, user_data.designation]):
            raise HTTPException(status_code=400, detail="All user fields are required")
        # Check if user already exists
        conn = get_connection()
        if not conn:
            raise HTTPException(status_code=500, detail="Database connection failed")
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_data.user_id,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User ID already exists")
        photos_dict = {photo.angle: photo.image_data for photo in photos_data}  # Convert photos list to dictionary for easier processing
        concatenated_embeddings = embedder.generate_user_embeddings(photos_dict)    # Generate concatenated embeddings for all 5 angles
        if not concatenated_embeddings:
            raise HTTPException(status_code=400, detail="Failed to generate face embeddings")
        # Store user data and embeddings in database
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, department, designation, embeddings)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_data.user_id,
                user_data.username,
                user_data.department,
                user_data.designation,
                concatenated_embeddings
            ))
            conn.commit()
        return JSONResponse(
            status_code=201,
            content={
                "message": "User registered successfully with face embeddings",
                "user_id": user_data.user_id,
                "photos_processed": len(photos_data),
                "embedding_dimensions": len(concatenated_embeddings)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete user registration"""
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")
            conn.commit()
        
        return JSONResponse(
            content={"message": "User deleted successfully"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    print("Starting server at http://0.0.0.0:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
