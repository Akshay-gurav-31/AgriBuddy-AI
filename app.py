from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import json

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # use env in production

# Supabase configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Gemini / Generative AI key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Create Supabase client with proper error handling
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to create Supabase client: {e}")
        supabase = None
else:
    print("Supabase URL or Key not configured. SUPABASE_URL/SUPABASE_KEY environment variables required.")

# Configure Gemini / Generative AI
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Initialize a default model object for simple text generation (if supported by your genai version)
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception:
            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
            except Exception:
                try:
                    model = genai.GenerativeModel("gemini")
                except Exception:
                    try:
                        model = genai.GenerativeModel("gemini-2.0")
                    except Exception:
                        model = None
    except Exception as e:
        print(f"Failed to configure Gemini API key: {e}")
        model = None
else:
    print("GEMINI_API_KEY is not set. Vision and text generation endpoints will be disabled.")
    model = None

@app.route("/")
def home():
    # Redirect to chat interface page by default
    return redirect(url_for('chat_interface'))

@app.route("/login")
def login():
    # Always clear session on login page to prevent automatic login
    session.clear()
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not supabase:
        return render_template("login.html", error="Authentication service not configured.")
    
    try:
        # Attempt to sign in directly - Supabase will handle validation
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Debug: Print the response to see what we're getting
        print("Supabase login response:", response)
        
        # Depending on supabase client version, "user" may be in different places
        user_obj = getattr(response, 'user', None) or (response.get('user') if isinstance(response, dict) else None)
        session_obj = getattr(response, 'session', None) or (response.get('session') if isinstance(response, dict) else None)
        
        if user_obj:
            # Check if user has confirmed their email
            email_confirmed = getattr(user_obj, 'email_confirmed_at', None) or user_obj.get('email_confirmed_at')
            if not email_confirmed:
                return render_template("login.html", error="Please confirm your email address. Check your inbox for the confirmation email.")
            
            # Set session variables
            session['logged_in'] = True
            session['user_id'] = getattr(user_obj, 'id', None) or user_obj.get('id')
            session['user_email'] = getattr(user_obj, 'email', None) or user_obj.get('email')
            
            # If we have a session token, store it as well
            if session_obj:
                session['access_token'] = getattr(session_obj, 'access_token', None) or session_obj.get('access_token')
            
            print("Login successful for user:", session['user_email'])
            return redirect(url_for('chat_interface'))
        else:
            return render_template("login.html", error="Invalid credentials")
    except Exception as e:
        print("Login error:", str(e))  # Debug: Print the actual error
        error_message = str(e).lower()
        if "invalid credentials" in error_message or "wrong" in error_message:
            return render_template("login.html", error="Invalid email or password. Please try again.")
        elif "email" in error_message and ("not confirmed" in error_message or "confirmation" in error_message):
            return render_template("login.html", error="Please confirm your email address. Check your inbox for the confirmation email.")
        elif "not found" in error_message or "no user" in error_message:
            return render_template("login.html", error="No account found with this email. Please sign up first.")
        else:
            return render_template("login.html", error="Login failed: " + str(e))

@app.route("/chat-interface")
def chat_interface():
    # Check if user is logged in properly
    if not session.get('logged_in') or not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/weather")
def weather():
    city = request.args.get('city')
    zip_code = request.args.get('zip')
    
    if zip_code:
        lat, lon, city_name = get_coordinates_by_zip(zip_code)
        if lat and lon:
            weather_info = get_weather_by_coordinates(lat, lon)
            # Add simulated forecast data
            forecast_data = generate_forecast_data()
            return jsonify({"city": city_name, "weather": weather_info, "forecast": forecast_data})
        else:
            # Graceful fallback: try direct weather API using ZIP if location fails
            weather_info = get_weather_by_zip(zip_code)
            if weather_info:
                # Add simulated forecast data
                forecast_data = generate_forecast_data()
                return jsonify({"zip": zip_code, "weather": weather_info, "forecast": forecast_data})
            return jsonify({"error": "Could not find location for ZIP code"}), 404
    elif city:
        weather_info = get_weather(city)
        # Add simulated forecast data
        forecast_data = generate_forecast_data()
        return jsonify({"city": city, "weather": weather_info, "forecast": forecast_data})
    else:
        return jsonify({"error": "City or ZIP code required"}), 400

def generate_forecast_data():
    """Generate simulated 5-day forecast data"""
    import random
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    conditions = [
        {'icon': 'fas fa-sun', 'desc': 'Sunny'},
        {'icon': 'fas fa-cloud-sun', 'desc': 'Partly Cloudy'},
        {'icon': 'fas fa-cloud', 'desc': 'Cloudy'},
        {'icon': 'fas fa-cloud-showers-heavy', 'desc': 'Rainy'},
        {'icon': 'fas fa-bolt', 'desc': 'Thunderstorms'}
    ]
    
    forecast = []
    base_temp = random.randint(25, 35)  # Base temperature for the week
    
    for i, day in enumerate(days):
        condition = random.choice(conditions)
        temp_variation = random.randint(-5, 5)
        temp = base_temp + temp_variation
        forecast.append({
            'day': day,
            'icon': condition['icon'],
            'temp': f'{temp}°C',
            'desc': condition['desc']
        })
    
    return forecast

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_post():
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')
    
    if password != confirm_password:
        return render_template("signup.html", error="Passwords do not match")
    
    if not supabase:
        return render_template("signup.html", error="Signup service not configured.")
    
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "first_name": first_name,
                    "last_name": last_name
                }
            }
        })
        
        user_obj = getattr(response, 'user', None) or (response.get('user') if isinstance(response, dict) else None)
        if user_obj:
            # After successful signup, show a message asking user to confirm email
            return render_template("login.html", success="Account created successfully! Please check your email to confirm your account before logging in.")
        else:
            return render_template("signup.html", error="Signup failed - Email may already be registered")
    except Exception as e:
        if "email" in str(e).lower() and "unique" in str(e).lower():
            return render_template("signup.html", error="Email already registered. Please use a different email or log in.")
        return render_template("signup.html", error="Signup failed: " + str(e))

@app.route("/logout")
def logout():
    try:
        if supabase:
            supabase.auth.sign_out()
    except Exception:
        pass
    # Clear all session data
    session.clear()
    # Also clear any potential cookies that might cause auto-login
    response = redirect(url_for('login'))
    response.set_cookie('session', '', expires=0)
    response.set_cookie('remember_token', '', expires=0)
    return response

@app.route("/chat", methods=["POST"])
def chat():
    if 'logged_in' not in session:
        return jsonify({"reply": "Please log in first"}), 401
    
    # Check if Supabase client is available
    if not supabase:
        return jsonify({"reply": "Database connection error. Please try again later."}), 500
    
    data = request.json
    if data is None:
        return jsonify({"reply": "Invalid request data"}), 400
    
    user_message = data.get("message", "")
    location = data.get("location", "")
    zip_code = data.get("zipCode", "")
    
    # Get user profile information
    profile_info = ""
    try:
        profile_data = supabase.table("profiles").select("*").eq("user_id", session['user_id']).execute()
        if profile_data.data:
            profile_record = profile_data.data[0]
            profile_info = f"Farmer Name: {profile_record.get('full_name', '')}"
            if profile_record.get('phone_number'):
                profile_info += f", Phone: {profile_record.get('phone_number')}"
            if profile_record.get('past_cultivation'):
                profile_info += f", Farm Info: {profile_record.get('past_cultivation')}"
            if profile_record.get('future_plans'):
                profile_info += f", Future Plans: {profile_record.get('future_plans')}"
            if profile_record.get('land_area'):
                profile_info += f", Land Size: {profile_record.get('land_area')} {profile_record.get('land_unit', 'acre')}"
            if profile_record.get('soil_type'):
                profile_info += f", Soil Type: {profile_record.get('soil_type')}"
            if profile_record.get('current_crops'):
                profile_info += f", Currently Grown Crops: {profile_record.get('current_crops')}"
            if profile_record.get('preferred_crops'):
                profile_info += f", Preferred Crops: {profile_record.get('preferred_crops')}"
            if profile_record.get('city') and profile_record.get('state'):
                profile_info += f", Location: {profile_record.get('city')}, {profile_record.get('state')}"
    except Exception as e:
        # Handle JWT/token errors specifically - only for auth-related issues
        error_str = str(e).lower()
        if "jwt" in error_str or "token" in error_str or "signature" in error_str or "malformed" in error_str:
            # Clear session and redirect to login only for auth errors
            session.pop('logged_in', None)
            session.pop('user_id', None)
            session.pop('user_email', None)
            return jsonify({"reply": "Session expired. Please log in again."}), 401
        print("Failed to fetch profile details:", str(e))
    
    weather_info = ""
    if zip_code:
        lat, lon, city_name = get_coordinates_by_zip(zip_code)
        if lat and lon:
            weather_info = get_weather_by_coordinates(lat, lon)
            location = city_name
    elif location:
        weather_info = get_weather(location)
        
    prompt = f"You are AgriBuddy, a helpful farmer assistant. {profile_info}. User says: '{user_message}'. "
    if weather_info:
        prompt += f"Current weather in {location}: {weather_info}. "

    # Fallback if model isn't configured
    if not model:
        reply_text = "AI assistant not configured. Please set GEMINI_API_KEY in environment."
    else:
        try:
            # use generate_content on the model if available; otherwise try genai.generate_text
            response = None
            try:
                response = model.generate_content(prompt)
                reply_text = getattr(response, 'text', None) or (response.get('text') if isinstance(response, dict) else str(response))
            except Exception:
                # fallback to genai.generate_text (depending on library version)
                try:
                    # The genai.generate_text method doesn't take positional arguments
                    # We need to use the correct method signature
                    resp = model.generate_content(prompt) if model else None
                    if resp:
                        reply_text = getattr(resp, 'text', None) or (resp.get('text') if isinstance(resp, dict) else str(resp))
                    else:
                        reply_text = "AI model not available for text generation"
                except Exception as e:
                    reply_text = "Failed to generate response: " + str(e)
        except Exception as e:
            reply_text = "Failed to generate response: " + str(e)
    
    try:
        # Create or get existing conversation
        conversations = supabase.table("conversations").select("*").eq("user_id", session['user_id']).order("updated_at", desc=True).limit(1).execute()
        
        if conversations.data:
            conversation_id = conversations.data[0]["id"]
        else:
            # Create new conversation
            new_conversation = supabase.table("conversations").insert({
                "user_id": session['user_id'],
                "title": user_message[:50] + "..." if len(user_message) > 50 else user_message
            }).execute()
            conversation_id = new_conversation.data[0]["id"]
        
        # Save user message
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "user",
            "content": user_message
        }).execute()
        
        # Save AI response
        supabase.table("messages").insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": reply_text
        }).execute()
        
        return jsonify({"reply": reply_text})
    except Exception as e:
        # Handle JWT/token errors specifically - only for auth-related issues
        error_str = str(e).lower()
        if "jwt" in error_str or "token" in error_str or "signature" in error_str or "malformed" in error_str:
            # Clear session and redirect to login only for auth errors
            session.pop('logged_in', None)
            session.pop('user_id', None)
            session.pop('user_email', None)
            return jsonify({"reply": "Session expired. Please log in again."}), 401
        print("Failed to save conversation:", str(e))
        return jsonify({"reply": reply_text})

@app.route("/farming-guide")
def farming_guide():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("farming_guide.html")

@app.route("/tutorials")
def tutorials():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("tutorials.html")


@app.route("/pest-control")
def pest_control():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("pest_control.html")

@app.route("/soil-analysis")
def soil_analysis():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("soil_analysis.html")

@app.route("/crop-recommendations")
def crop_recommendations():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("crop_recommendations.html")

@app.route("/pest-checker")
def pest_checker():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("pest_checker.html")

@app.route("/pest-checker", methods=["POST"])
def pest_checker_post():
    if 'logged_in' not in session:
        return jsonify({"error": "Please log in first"}), 401
    
    # Check if Gemini API key is available
    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500
    
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({"error": "No image file selected"}), 400
    
    # Check if file is an image (guard against None)
    content_type = getattr(file, 'content_type', None)
    if not content_type or not content_type.startswith('image/'):
        return jsonify({"error": "Invalid file type. Please upload an image file"}), 400
    
    try:
        # Read image file
        image_data = file.read()
        
        # Create prompt for Gemini API
        prompt = (
            "You are an agricultural expert AI assistant specialized in plant pest and disease identification. "
            "Analyze the provided image and return a JSON object with fields: is_agricultural (bool), is_relevant (bool), "
            "identified_as (string), name (string), type (Pest/Disease/Other), description (string), severity (Low/Medium/High/Critical), "
            "affected_crops (string), solutions (array of strings), prevention (array of strings)."
        )
        
        # Call Gemini 2.0 Vision model
        try:
            # Use Gemini 2.0 Flash model
            vision_model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception:
            # Fallback to gemini-1.5-flash if gemini-2.0-flash is not available
            try:
                vision_model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                # Fallback to gemini-pro-vision if newer models are not available
                try:
                    vision_model = genai.GenerativeModel('gemini-pro-vision')
                except Exception:
                    vision_model = None
        
        if not vision_model:
            return jsonify({"error": "Vision model not available in configured GenAI library."}), 500
        
        # Prepare the content for Gemini API
        image_part = {
            'mime_type': content_type,
            'data': image_data
        }
        
        # Generate content using Gemini
        response = vision_model.generate_content([prompt, image_part])
        
        # Attempt to parse JSON from response text
        resp_text = getattr(response, 'text', None) or (response.get('text') if isinstance(response, dict) else str(response))
        
        # Ensure resp_text is valid before attempting to parse JSON
        if not resp_text or not isinstance(resp_text, (str, bytes, bytearray)):
            return jsonify({
                "is_agricultural": True,
                "is_relevant": True,
                "name": "Analysis Completed",
                "type": "Information",
                "description": "No valid response text received from AI analysis",
                "severity": "N/A",
                "affected_crops": "Various",
                "solutions": ["Please consult with an agricultural expert for detailed analysis"],
                "prevention": ["Regular monitoring of crops", "Maintain proper hygiene in farming areas"]
            })
        
        try:
            # Clean up the response text to extract JSON
            cleaned_resp_text = resp_text.strip()
            
            # Remove markdown code block wrappers if present
            if cleaned_resp_text[:7] == "```json":
                cleaned_resp_text = cleaned_resp_text[7:]  # Remove ```json
            if cleaned_resp_text[:3] == "```":
                cleaned_resp_text = cleaned_resp_text[3:]  # Remove ```
            if cleaned_resp_text[-3:] == "```":
                cleaned_resp_text = cleaned_resp_text[:-3]  # Remove ```
            
            # Parse the JSON
            result = json.loads(cleaned_resp_text)
            
            # Ensure solutions and prevention are lists
            if 'solutions' in result and isinstance(result['solutions'], str):
                result['solutions'] = [result['solutions']]
            if 'prevention' in result and isinstance(result['prevention'], str):
                result['prevention'] = [result['prevention']]
                
            return jsonify(result)
        except json.JSONDecodeError as e:
            # Return a structured fallback with the raw response
            return jsonify({
                "is_agricultural": True,
                "is_relevant": True,
                "name": "Analysis Completed",
                "type": "Information",
                "description": f"Raw response from AI: {resp_text}",
                "severity": "N/A",
                "affected_crops": "Various",
                "solutions": ["Please consult with an agricultural expert for detailed analysis"],
                "prevention": ["Regular monitoring of crops", "Maintain proper hygiene in farming areas"]
            })
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return jsonify({"error": "Failed to process image. Please try again.", "detail": str(e)}), 500

@app.route("/test-session")
def test_session():
    return jsonify({
        "session": dict(session),
        "logged_in": session.get('logged_in', False),
        "user_id": session.get('user_id', None),
        "user_email": session.get('user_email', None)
    })

@app.route("/weather-dashboard")
def weather_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("weather_dashboard.html")

# ---------- FIXED WEATHER FUNCTIONS ----------

def get_weather(city):
    if not OPENWEATHER_API_KEY:
        return "OpenWeather API key not configured."
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=8)
        data = res.json()
        if str(data.get("cod")) == '200':
            visibility = data.get("visibility", None)
            if visibility:
                visibility = visibility / 1000  # Convert from meters to kilometers
            
            return {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"].get("pressure", None),
                "visibility": visibility,
                "uv_index": data.get("uvi", None),
                "wind_gust": data["wind"].get("gust", None)
            }
        else:
            return "Weather data not available."
    except Exception:
        return "Error fetching weather."

def get_coordinates_by_zip(zip_code):
    if not OPENWEATHER_API_KEY:
        return None, None, None
    try:
        # Use the ZIP-specific API for better accuracy in India
        url = f"https://api.openweathermap.org/geo/1.0/zip?zip={zip_code},IN&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=8)
        data = res.json()
        if "lat" in data and "lon" in data:
            lat = data["lat"]
            lon = data["lon"]
            name = data.get("name", f"ZIP {zip_code}")
            return lat, lon, name
        else:
            return None, None, None
    except Exception as e:
        print("Error fetching coordinates:", str(e))
        return None, None, None

def get_weather_by_coordinates(lat, lon):
    if not OPENWEATHER_API_KEY:
        return "OpenWeather API key not configured."
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=8)
        data = res.json()
        if str(data.get("cod")) == '200':
            visibility = data.get("visibility", None)
            if visibility:
                visibility = visibility / 1000  # Convert from meters to kilometers
            
            return {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"].get("pressure", None),
                "visibility": visibility,
                "uv_index": data.get("uvi", None),
                "wind_gust": data["wind"].get("gust", None)
            }
        else:
            return "Weather data not available."
    except Exception:
        return "Error fetching weather."

def get_weather_by_zip(zip_code):
    """Fallback direct weather fetch if coordinates not found"""
    if not OPENWEATHER_API_KEY:
        return None
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?zip={zip_code},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=8)
        data = res.json()
        if str(data.get("cod")) == '200':
            visibility = data.get("visibility", None)
            if visibility:
                visibility = visibility / 1000  # Convert from meters to kilometers
            
            return {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "pressure": data["main"].get("pressure", None),
                "visibility": visibility,
                "uv_index": data.get("uvi", None),
                "wind_gust": data["wind"].get("gust", None)
            }
        else:
            return None
    except Exception as e:
        print("Error fetching weather by ZIP:", str(e))
        return None

# --------------------------------------------

if __name__ == "__main__":
    # Use 0.0.0.0 for dev accessibility if needed. In production use a proper WSGI server.
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))