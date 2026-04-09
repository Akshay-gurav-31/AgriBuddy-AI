from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response, stream_with_context, send_file
import google.generativeai as genai
import requests
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import json
import base64
import hashlib
from datetime import datetime, timezone, timedelta
import time

try:
    from cryptography.fernet import Fernet
except Exception:
    Fernet = None

try:
    from groq import Groq
except ImportError:
    Groq = None

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # use env in production

# Supabase configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Gemini / Generative AI key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Community feature toggles (easy true/false control via .env)
COMMUNITY_ENCRYPTION_ENABLED = os.getenv("COMMUNITY_ENCRYPTION_ENABLED", "true").lower() == "true"
COMMUNITY_AUTO_DELETE_ENABLED = os.getenv("COMMUNITY_AUTO_DELETE_ENABLED", "false").lower() == "true"
COMMUNITY_AUTO_DELETE_HOURS = int(os.getenv("COMMUNITY_AUTO_DELETE_HOURS", "24"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if Groq and GROQ_API_KEY else None

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

gemini_client = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = True
    except Exception as e:
        print(f"Failed to configure Gemini API key: {e}")
else:
    print("GEMINI_API_KEY is not set. Gemini features will be disabled.")

@app.route("/")
def home():
    # Render the professional landing page for all visitors
    return render_template("landing.html", active_page='home')

@app.route("/login")
def login():
    # If already logged in, redirect to dashboard
    if session.get('logged_in'):
        return redirect(url_for('chat_interface'))
    # Always clear session on login page to prevent automatic login if they explicitly come here
    # (Optional: might want to skip clear if we redirect above)
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
            
            # Fetch user name from profiles table for the navbar
            try:
                profile_res = supabase.table("profiles").select("full_name").eq("user_id", session['user_id']).execute()
                if profile_res.data:
                    session['user_name'] = profile_res.data[0].get('full_name', 'User')
                else:
                    session['user_name'] = 'Farmer'
            except Exception as pe:
                print("Profile fetch error during login:", str(pe))
                session['user_name'] = 'Farmer'
            
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
    return render_template("index.html", active_page='chat')

@app.route("/api/profile")
def get_user_profile():
    if not session.get('logged_in') or not session.get('user_id'):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        profile_data = supabase.table("profiles").select("*").eq("user_id", session['user_id']).execute()
        if profile_data.data:
            return jsonify({"success": True, "profile": profile_data.data[0], "email": session.get('user_email')})
        else:
            return jsonify({"success": False, "error": "Profile not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/weather")
def weather():
    city = request.args.get('city')
    zip_code = request.args.get('zip')
    
    if zip_code:
        lat, lon, city_name = get_coordinates_by_zip(zip_code)
        if lat and lon:
            weather_info = get_weather_by_coordinates(lat, lon)
            forecast_data = get_forecast_by_lat_lon(lat, lon)
            aqi_info = get_air_quality(lat, lon)
            return jsonify({
                "city": city_name, 
                "weather": weather_info, 
                "forecast": forecast_data, 
                "aqi": aqi_info
            })
        else:
            weather_info = get_weather_by_zip(zip_code)
            if weather_info:
                return jsonify({"zip": zip_code, "weather": weather_info, "forecast": generate_forecast_data(), "aqi": None})
            return jsonify({"error": "Could not find location for ZIP code"}), 404
    elif city:
        lat, lon, city_name = get_coordinates_by_city(city)
        if lat and lon:
            weather_info = get_weather_by_coordinates(lat, lon)
            forecast_data = get_forecast_by_lat_lon(lat, lon)
            aqi_info = get_air_quality(lat, lon)
            return jsonify({
                "city": city_name, 
                "weather": weather_info, 
                "forecast": forecast_data, 
                "aqi": aqi_info
            })
        else:
            weather_info = get_weather(city)
            forecast_data = generate_forecast_data()
            return jsonify({"city": city, "weather": weather_info, "forecast": forecast_data, "aqi": None})
    else:
        return jsonify({"error": "City or ZIP code required"}), 400

def generate_forecast_data():
    """Generate simulated 5-day forecast data using actual upcoming days"""
    import random
    from datetime import datetime, timedelta
    
    # Get current day plus next 4 days
    today = datetime.now()
    days = [(today + timedelta(days=i)).strftime('%a') for i in range(5)]
    
    conditions = [
        {'icon': 'fas fa-sun', 'desc': 'Sunny'},
        {'icon': 'fas fa-cloud-sun', 'desc': 'Partly Cloudy'},
        {'icon': 'fas fa-cloud', 'desc': 'Cloudy'},
        {'icon': 'fas fa-cloud-showers-heavy', 'desc': 'Rainy'},
        {'icon': 'fas fa-bolt', 'desc': 'Thunderstorms'}
    ]
    
    forecast = []
    base_temp = random.randint(25, 35)
    
    for day in days:
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
    if session.get('logged_in'):
        return redirect(url_for('chat_interface'))
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

@app.route("/auth/callback")
def auth_callback():
    """
    Supabase email confirmation redirect handler.
    Supabase sends tokens in the URL hash fragment (client-side only),
    so we serve a small HTML page that extracts the token and POSTs it to /auth/set-session.
    """
    return render_template("auth_callback.html")

@app.route("/auth/set-session", methods=["POST"])
def auth_set_session():
    """
    Receives access_token from client-side after email confirmation,
    verifies with Supabase and sets Flask session, then redirects to home.
    """
    data = request.json
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    if not access_token or not supabase:
        return jsonify({"error": "Invalid token"}), 400

    try:
        # Set the session in Supabase client using the token
        auth_response = supabase.auth.set_session(access_token, refresh_token)
        user_obj = getattr(auth_response, 'user', None)

        if user_obj:
            session['logged_in'] = True
            session['user_id'] = getattr(user_obj, 'id', None)
            session['user_email'] = getattr(user_obj, 'email', None)
            session['access_token'] = access_token
            return jsonify({"redirect": url_for('chat_interface')})
        else:
            return jsonify({"error": "Could not verify user"}), 400
    except Exception as e:
        print("Auth callback error:", str(e))
        return jsonify({"error": str(e)}), 400

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

    # Handle AI Response with fallback models (Groq Primary, Gemini Fallback)
    reply_text = "AI model is currently busy. Please try again in 1 minute."
    
    # 1. Try Groq first (Much faster and higher limits)
    if groq_client:
        try:
            # Using the model suggested in curl or high-quality llama
            model_to_use = "llama-3.3-70b-versatile" 
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_to_use,
            )
            reply_text = chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq chat failed, falling back to Gemini: {e}")
            # Fallback to Gemini if Groq fails
            if GEMINI_API_KEY:
                models_to_try = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
                for model_name in models_to_try:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(prompt)
                        reply_text = getattr(response, 'text', None) or (response.get('text') if isinstance(response, dict) else str(response))
                        if reply_text:
                            break
                    except Exception as gemini_e:
                        print(f"Gemini fallback {model_name} failed: {gemini_e}")
                        continue
    elif GEMINI_API_KEY:
        # If Groq not configured, use Gemini
        models_to_try = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                reply_text = getattr(response, 'text', None) or (response.get('text') if isinstance(response, dict) else str(response))
                if reply_text:
                    break
            except Exception as e:
                continue
    else:
        reply_text = "AI Features are currently disabled (API keys not set)."
    
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
    return render_template("farming_guide.html", active_page='farming_guide')

@app.route("/tutorials")
def tutorials():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("tutorials.html", active_page='tutorials')


@app.route("/pest-control")
def pest_control():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("pest_control.html", active_page='pest_control')

@app.route("/soil-analysis")
def soil_analysis():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("soil_analysis.html", active_page='soil_analysis')

@app.route("/crop-recommendations")
def crop_recommendations():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("crop_recommendations.html", active_page='crop_recommendations')

@app.route("/pest-checker")
def pest_checker():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template("pest_checker.html", active_page='pest_checker')

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
        
        # Attempt Groq Vision First
        if groq_client:
            try:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                vision_completion = groq_client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt + " Return ONLY the JSON object."},
                                {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{base64_image}"}}
                            ]
                        }
                    ],
                    model="llama-3.2-90b-vision-preview",
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                resp_text = vision_completion.choices[0].message.content
                if resp_text:
                    result = json.loads(resp_text)
                    # Cleanup solutions/prevention
                    if 'solutions' in result and isinstance(result['solutions'], str): result['solutions'] = [result['solutions']]
                    if 'prevention' in result and isinstance(result['prevention'], str): result['prevention'] = [result['prevention']]
                    return jsonify(result)
            except Exception as e:
                print(f"Groq Vision failed, falling back to Gemini: {e}")

        # Fallback to Gemini models in order
        models_to_try = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-pro-latest']
        last_error = None
        
        # Prepare the content for Gemini API
        image_part = {"mime_type": content_type, "data": image_data}
        
        for model_name in models_to_try:
            try:
                # Generate content using Gemini
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([prompt, image_part])
                
                # Attempt to parse JSON from response text
                resp_text = getattr(response, 'text', None) or (response.get('text') if isinstance(response, dict) else str(response))
                
                if not resp_text: continue
                
                cleaned_resp_text = resp_text.strip()
                if cleaned_resp_text[:7] == "```json": cleaned_resp_text = cleaned_resp_text[7:]
                if cleaned_resp_text[:3] == "```": cleaned_resp_text = cleaned_resp_text[3:]
                if cleaned_resp_text[-3:] == "```": cleaned_resp_text = cleaned_resp_text[:-3]
                
                result = json.loads(cleaned_resp_text)
                if 'solutions' in result and isinstance(result['solutions'], str): result['solutions'] = [result['solutions']]
                if 'prevention' in result and isinstance(result['prevention'], str): result['prevention'] = [result['prevention']]
                return jsonify(result)
            except Exception as e:
                last_error = str(e)
                continue

        # If we get here, all models failed
        if "429" in (last_error or ""):
            return jsonify({"error": "AI Rate Limit Reached. The free tier quota for image analysis has been exceeded. Please try again in a few minutes or use a different API key."}), 429
        
        return jsonify({
            "is_agricultural": True,
            "is_relevant": True,
            "name": "Analysis Refined",
            "type": "Information",
            "description": "The AI is currently processing many requests. While a specific diagnosis could not be generated, please ensure your plant has proper sunlight and water.",
            "severity": "Low",
            "affected_crops": "General",
            "solutions": ["Ensure optimal growing conditions", "Monitor for changes in symptoms"],
            "prevention": ["Regular cleaning of tools", "Quarantine new plants"]
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
    # Check if user is logged in properly
    if not session.get('logged_in') or not session.get('user_id'):
        return redirect(url_for('login'))
        
    # Check if user has updated their profile
    # If using Supabase, we would check if a record exists in farmer_details
    profile_updated = False
    try:
        user_id = session.get('user_id')
        response = supabase.table('farmer_details').select('*').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            profile_updated = True
    except Exception as e:
        print("Error checking profile:", e)

    return render_template("weather_dashboard.html", active_page='dashboard', profile_updated=profile_updated)

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
                "sunrise": data.get("sys", {}).get("sunrise"),
                "sunset": data.get("sys", {}).get("sunset"),
                "timezone": data.get("timezone"),
                "clouds": data.get("clouds", {}).get("all", 0),
                "moon": calculate_moon_phase(),
                "uv_index": data.get("uvi", None)
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
                "sunrise": data.get("sys", {}).get("sunrise"),
                "sunset": data.get("sys", {}).get("sunset"),
                "timezone": data.get("timezone"),
                "clouds": data.get("clouds", {}).get("all", 0),
                "moon": calculate_moon_phase(),
                "uv_index": data.get("uvi", None)
            }
        else:
            return "Weather data not available."
    except Exception:
        return "Error fetching weather."

def calculate_moon_phase():
    """Calculate the current moon phase and illumination"""
    from datetime import datetime
    import math
    
    # Reference: 2000-01-06 18:14:00 was a new moon
    ref_date = datetime(2000, 1, 6, 18, 14, 0)
    now = datetime.utcnow()
    diff = now - ref_date
    days = diff.days + diff.seconds / 86400.0
    
    # Moon cycle is approx 29.530588853 days
    cycle = 29.530588853
    phase_pos = (days % cycle) / cycle
    
    # 0 = New Moon, 0.25 = First Quarter, 0.5 = Full Moon, 0.75 = Last Quarter
    illumination = 1.0 - math.cos(phase_pos * 2.0 * math.pi)
    illumination = (illumination / 2.0) * 100
    
    if phase_pos < 0.03 or phase_pos > 0.97:
        phase_name = "New Moon"
        icon = "🌑"
    elif phase_pos < 0.22:
        phase_name = "Waxing Crescent"
        icon = "🌒"
    elif phase_pos < 0.28:
        phase_name = "First Quarter"
        icon = "🌓"
    elif phase_pos < 0.47:
        phase_name = "Waxing Gibbous"
        icon = "🌔"
    elif phase_pos < 0.53:
        phase_name = "Full Moon"
        icon = "🌕"
    elif phase_pos < 0.72:
        phase_name = "Waning Gibbous"
        icon = "🌖"
    elif phase_pos < 0.78:
        phase_name = "Last Quarter"
        icon = "🌗"
    else:
        phase_name = "Waning Crescent"
        icon = "🌘"
        
    return {
        "phase": phase_name,
        "illumination": round(illumination),
        "icon": icon
    }

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
                "sunrise": data.get("sys", {}).get("sunrise"),
                "sunset": data.get("sys", {}).get("sunset"),
                "timezone": data.get("timezone"),
                "clouds": data.get("clouds", {}).get("all", 0),
                "moon": calculate_moon_phase(),
                "uv_index": data.get("uvi", None)
            }
        else:
            return None
    except Exception as e:
        print("Error fetching weather by ZIP:", str(e))
        return None

def get_coordinates_by_city(city):
    if not OPENWEATHER_API_KEY:
        return None, None, None
    try:
        url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=8)
        data = res.json()
        if data and len(data) > 0:
            return data[0]["lat"], data[0]["lon"], data[0].get("name", city)
        return None, None, None
    except Exception:
        return None, None, None

def get_forecast_by_lat_lon(lat, lon):
    if not OPENWEATHER_API_KEY:
        return generate_forecast_data()
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=8)
        data = res.json()
        if str(data.get("cod")) == '200':
            forecast_list = []
            for item in data.get("list", [])[:16]:  # Next 48 hours (every 3 hours)
                forecast_list.append({
                    "dt": item.get("dt"),
                    "dt_txt": item.get("dt_txt"),
                    "temp": item["main"]["temp"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"],
                    "description": item["weather"][0]["description"],
                    "icon_code": item["weather"][0]["icon"]
                })
            return forecast_list
        return generate_forecast_data()
    except Exception as e:
        print("Error fetching real forecast:", str(e))
        return generate_forecast_data()

def get_air_quality(lat, lon):
    if not OPENWEATHER_API_KEY:
        return None
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        res = requests.get(url, timeout=8)
        data = res.json()
        if data and "list" in data:
            item = data["list"][0]
            return {
                "aqi": item["main"]["aqi"],
                "pm2_5": item["components"]["pm2_5"],
                "pm10": item["components"]["pm10"],
                "no2": item["components"]["no2"],
                "o3": item["components"]["o3"]
            }
        return None
    except Exception as e:
        print("Error fetching AQI:", str(e))
        return None

# --------------------------------------------
# COMMUNITY ROUTES
# --------------------------------------------

# In-memory store as fallback (works without Supabase community_posts table)
_community_posts = []
_community_event_seq = 0
_community_latest_event = None
_community_typing_users = {}
COMMUNITY_DELETED_MARKER = "__DELETED__"

def _build_community_cipher():
    """
    Build Fernet cipher for community chat encryption.
    Priority:
    1) COMMUNITY_ENCRYPTION_KEY from env (recommended)
    2) Derived key from FLASK_SECRET_KEY (fallback)
    """
    if not COMMUNITY_ENCRYPTION_ENABLED or Fernet is None:
        return None

    raw_key = os.getenv("COMMUNITY_ENCRYPTION_KEY", "").strip()
    if raw_key:
        try:
            return Fernet(raw_key.encode("utf-8"))
        except Exception:
            print("Invalid COMMUNITY_ENCRYPTION_KEY. Falling back to derived key.")

    secret = os.getenv("FLASK_SECRET_KEY", "your-secret-key-here").encode("utf-8")
    derived = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(derived)

_community_cipher = _build_community_cipher()

def _encrypt_community_text(value):
    if not value:
        return value
    if not COMMUNITY_ENCRYPTION_ENABLED or not _community_cipher:
        return value
    return _community_cipher.encrypt(value.encode("utf-8")).decode("utf-8")

def _decrypt_community_text(value):
    if not value:
        return value
    if not COMMUNITY_ENCRYPTION_ENABLED or not _community_cipher:
        return value
    try:
        return _community_cipher.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # Handles old plain-text rows or corrupted encrypted text safely.
        return value

def _cleanup_expired_community_posts():
    if not COMMUNITY_AUTO_DELETE_ENABLED:
        return

    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=COMMUNITY_AUTO_DELETE_HOURS)
    cutoff_iso = cutoff_dt.isoformat()

    # Cleanup in DB
    if supabase:
        try:
            supabase.table("community_posts").delete().lt("created_at", cutoff_iso).execute()
        except Exception as e:
            print("Community cleanup DB error:", str(e))

    # Cleanup in memory fallback
    global _community_posts
    filtered = []
    for p in _community_posts:
        created_raw = p.get("created_at")
        try:
            created_dt = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
        except Exception:
            # If timestamp is malformed, keep it to avoid accidental data loss.
            filtered.append(p)
            continue
        if created_dt >= cutoff_dt:
            filtered.append(p)
    _community_posts = filtered

def _community_username_from_session():
    email = (session.get("user_email") or "anonymous@example.com").strip().lower()
    base = email.split("@")[0]
    sanitized = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in base).strip("._-")
    if not sanitized:
        sanitized = "user"
    unique_suffix = hashlib.sha1(email.encode("utf-8")).hexdigest()[:4]
    return f"{sanitized}_{unique_suffix}"

def _publish_community_event(event_type, payload):
    global _community_event_seq, _community_latest_event
    _community_event_seq += 1
    _community_latest_event = {
        "seq": _community_event_seq,
        "type": event_type,
        "payload": payload
    }

@app.route("/community")
def community():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("community.html", community_username=_community_username_from_session(), active_page='community')

@app.route("/community/logo")
def community_logo():
    # Serve custom community logo from local project images folder.
    logo_path = os.path.join(app.root_path, "images", "agri-buddy.png")
    if os.path.exists(logo_path):
        return send_file(logo_path, mimetype="image/png")
    return "", 404

@app.route("/community/messages")
def community_messages():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    _cleanup_expired_community_posts()

    try:
        limit = int(request.args.get("limit", 15))
    except Exception:
        limit = 15
    limit = max(1, min(limit, 50))
    before = request.args.get("before")

    posts = []
    members_set = {}
    has_more = False

    # Try Supabase first
    if supabase:
        try:
            query = supabase.table("community_posts").select("*")
            if before:
                query = query.lt("created_at", before)
            # Fetch one extra row to detect if older messages still exist.
            res = query.order("created_at", desc=True).limit(limit + 1).execute()
            if res.data:
                posts = res.data
        except Exception as e:
            print("Community Supabase error (using memory):", str(e))

    # Fallback to in-memory
    if not posts:
        fallback_posts = _community_posts
        if before:
            filtered = []
            for p in fallback_posts:
                created = p.get("created_at")
                if created and str(created) < str(before):
                    filtered.append(p)
            fallback_posts = filtered
        posts = fallback_posts[-(limit + 1):]

    if len(posts) > limit:
        has_more = True
        posts = posts[:limit]

    # Ensure chronological order in API response.
    posts = list(reversed(posts))

    # Decrypt message/image payloads before sending to frontend.
    normalized_posts = []
    for p in posts:
        post_copy = dict(p)
        post_copy["message"] = _decrypt_community_text(post_copy.get("message"))
        post_copy["image_url"] = _decrypt_community_text(post_copy.get("image_url"))
        normalized_posts.append(post_copy)

    # Build members list from posts + current user
    for p in normalized_posts:
        u = p.get('username', 'unknown')
        if u not in members_set:
            members_set[u] = True

    current_username = _community_username_from_session()
    members_set[current_username] = True

    members = [{"username": u, "is_you": (u == current_username)} for u in members_set]

    return jsonify({"messages": normalized_posts, "members": members, "has_more": has_more})

@app.route("/community/post", methods=["POST"])
def community_post():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    _cleanup_expired_community_posts()

    data = request.json or {}
    message = (data.get('message') or '').strip()
    image_b64 = data.get('image_b64')

    # Validation
    if not message and not image_b64:
        return jsonify({"error": "Message or image required"}), 400
    if len(message) > 500:
        return jsonify({"error": "Message too long (max 500 characters)"}), 400

    username = _community_username_from_session()
    user_id = session.get('user_id', 'anonymous')

    image_url = None
    if image_b64:
        # Validate image payload strictly: PNG/JPG/JPEG only, max 10MB.
        try:
            image_bytes = base64.b64decode(image_b64, validate=True)
        except Exception:
            return jsonify({"error": "Invalid image data"}), 400

        max_image_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_image_size:
            return jsonify({"error": "Image must be 10MB or less"}), 400

        mime_type = None
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            mime_type = "image/png"
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            mime_type = "image/jpeg"
        else:
            return jsonify({"error": "Only PNG/JPG/JPEG images are allowed"}), 400

        # Store as data URL (works without external storage)
        image_url = f"data:{mime_type};base64,{image_b64}"

    encrypted_message = _encrypt_community_text(message)
    encrypted_image_url = _encrypt_community_text(image_url)

    post = {
        "id": str(len(_community_posts) + 1),
        "username": username,
        "user_id": user_id,
        "message": encrypted_message,
        "image_url": encrypted_image_url,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Try to save to Supabase
    saved_to_db = False
    if supabase:
        try:
            db_post = {
                "username": username,
                "user_id": user_id,
                "message": encrypted_message,
                "image_url": encrypted_image_url,
                "created_at": post["created_at"]
            }
            res = supabase.table("community_posts").insert(db_post).execute()
            if res.data and len(res.data) > 0 and res.data[0].get("id"):
                post["id"] = str(res.data[0]["id"])
            saved_to_db = True
        except Exception as e:
            print("Community post DB error (using memory):", str(e))

    if not saved_to_db:
        _community_posts.append(post)

    public_post = dict(post)
    public_post["message"] = _decrypt_community_text(public_post.get("message"))
    public_post["image_url"] = _decrypt_community_text(public_post.get("image_url"))
    _publish_community_event("new_message", public_post)
    _community_typing_users.pop(username, None)
    _publish_community_event("typing", {"username": username, "is_typing": False})

    return jsonify({"success": True, "message": public_post})

@app.route("/community/typing", methods=["POST"])
def community_typing():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json or {}
    is_typing = bool(data.get("is_typing", True))
    username = _community_username_from_session()

    if is_typing:
        _community_typing_users[username] = time.time()
    else:
        _community_typing_users.pop(username, None)

    _publish_community_event("typing", {"username": username, "is_typing": is_typing})
    return jsonify({"success": True})

@app.route("/community/delete/<post_id>", methods=["POST", "DELETE"])
def community_delete(post_id):
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    user_id = str(session.get("user_id", ""))
    if not user_id:
        return jsonify({"error": "Invalid user session"}), 401

    deleted = False
    current_username = _community_username_from_session()
    tombstone_message = _encrypt_community_text(COMMUNITY_DELETED_MARKER)
    tombstone_image = None

    # Try DB soft-delete with explicit ownership verification first.
    if supabase:
        try:
            row_res = (
                supabase.table("community_posts")
                .select("id,user_id")
                .eq("id", post_id)
                .limit(1)
                .execute()
            )

            if row_res.data and len(row_res.data) > 0:
                owner_id = str(row_res.data[0].get("user_id", ""))
                if owner_id != user_id:
                    return jsonify({"error": "Message not found or not yours"}), 404

                # Soft delete (tombstone) the post from the database.
                access_token = session.get('access_token')
                if access_token:
                    auth_client = create_client(SUPABASE_URL, SUPABASE_KEY)
                    auth_client.postgrest.auth(access_token)
                    del_res = auth_client.table("community_posts").update({"message": tombstone_message, "image_url": tombstone_image}).eq("id", post_id).execute()
                else:
                    del_res = supabase.table("community_posts").update({"message": tombstone_message, "image_url": tombstone_image}).eq("id", post_id).execute()
                
                if del_res.data and len(del_res.data) > 0:
                    deleted = True
                else:
                    print("Supabase update returned empty (RLS block or not found).")
        except Exception as e:
            print("Community delete DB error:", str(e))

    # Update in in-memory list if present.
    global _community_posts
    for p in _community_posts:
        if str(p.get("id")) == str(post_id) and (
            str(p.get("user_id")) == user_id or str(p.get("username")) == current_username
        ):
            p["message"] = tombstone_message
            p["image_url"] = tombstone_image
            deleted = True

    if not deleted:
        return jsonify({"error": "Message not found or not yours"}), 404

    _publish_community_event("message_deleted", {"id": str(post_id), "username": current_username})
    return jsonify({"success": True})

@app.route("/community/stream")
def community_stream():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    @stream_with_context
    def event_stream():
        last_seen_seq = _community_event_seq
        # Send initial connect event so client knows stream is live.
        yield "event: connected\ndata: {}\n\n"

        while True:
            if _community_latest_event and _community_latest_event["seq"] > last_seen_seq:
                last_seen_seq = _community_latest_event["seq"]
                yield f"event: message\ndata: {json.dumps(_community_latest_event)}\n\n"
            else:
                # Keep connection alive.
                yield "event: ping\ndata: {}\n\n"

            time.sleep(0.5)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

# --------------------------------------------

if __name__ == "__main__":
    # Use 0.0.0.0 for dev accessibility if needed. In production use a proper WSGI server.
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))