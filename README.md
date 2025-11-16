# AgriBuddy - Smart Farming Assistant

AgriBuddy is a comprehensive agricultural assistant application designed to help farmers with crop recommendations, pest control, weather insights, and farming guidance. The application features a chatbot interface powered by AI, along with specialized tools for various farming needs.

## Tech Stack

### Backend
- **Python Flask**: Web framework for building the application
- **Supabase**: Backend-as-a-Service (BaaS) for database and authentication
- **Google Generative AI (Gemini)**: AI models for chatbot and image analysis
- **OpenWeatherMap API**: Weather data and geocoding services

### Frontend
- **HTML/CSS/JavaScript**: Core frontend technologies
- **Chart.js**: Data visualization for weather analytics
- **Font Awesome**: Icon library for UI elements

### Database
- **PostgreSQL**: Relational database provided by Supabase
- **Row Level Security (RLS)**: Data isolation and security policies

## Required API Keys

To run AgriBuddy, you'll need the following API keys:

1. **Google Generative AI (Gemini) API Key**
   - Used for AI chat responses and pest/disease image analysis
   - Model preference: `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-pro` → `gemini-1.5-pro`

2. **OpenWeatherMap API Key**
   - Used for weather data and location-based services
   - Provides real-time weather information and forecasts

3. **Supabase URL and Anon Key**
   - Used for database operations and user authentication
   - Provides secure access to PostgreSQL database

## Database Schema

The application uses three main tables:

### 1. Profiles Table
Stores user profile information:
- `id`: UUID (Primary Key)
- `user_id`: Foreign key to auth.users
- `full_name`: User's full name
- `phone_number`: Contact information
- `state`, `city`, `region`: Location details
- `crops`: JSONB array of crops
- `land_area` and `land_unit`: Farm size information
- `past_cultivation`, `future_plans`: Farming history and plans
- `water_source`, `soil_type`: Farming conditions
- `current_crops`, `preferred_crops`: Crop preferences
- `preferred_language`: Language preference
- `created_at`, `updated_at`: Timestamps

### 2. Conversations Table
Stores chat conversation metadata:
- `id`: UUID (Primary Key)
- `created_at`, `updated_at`: Timestamps
- `title`: Conversation title
- `user_id`: Foreign key to user

### 3. Messages Table
Stores individual chat messages:
- `id`: UUID (Primary Key)
- `conversation_id`: Foreign key to conversations
- `role`: Message sender (user/assistant)
- `content`: Message content
- `created_at`: Timestamp

## Application Features and Pages

### 1. Authentication System
- **Login (`/login`)**: Secure user authentication with email/password
- **Signup (`/signup`)**: New user registration with profile creation
- **Logout (`/logout`)**: Secure session termination

### 2. Chat Interface (`/chat-interface`)
The main dashboard featuring:
- AI-powered farming assistant chatbot
- Context-aware responses based on user profile
- Weather integration in conversations
- Message history storage
- Location-based weather queries (city or ZIP code)

### 3. Weather Dashboard (`/weather-dashboard`)
Comprehensive weather insights:
- Real-time weather data for any location
- 5-day weather forecast
- Temperature and precipitation charts
- Climate statistics (temperature, humidity, wind speed)
- Real-time clock display
- Responsive grid layout with multiple data visualizations

### 4. Pest Checker (`/pest-checker`)
AI-powered pest and disease identification:
- Image upload functionality for plant photos
- Computer vision analysis using Gemini 2.0 Vision model
- Identification of pests, diseases, and other plant issues
- Severity assessment and affected crops information
- Solutions and prevention recommendations

### 5. Pest Control Guide (`/pest-control`)
Integrated Pest Management (IPM) strategies:
- Biological control methods
- Cultural practices
- Chemical control options
- Monitoring and scouting techniques
- Database of common pests and solutions

### 6. Soil Analysis (`/soil-analysis`)
Soil health assessment tool:
- Recommendations based on pH levels and organic matter
- Ideal soil parameters for major crops
- Soil improvement guides

### 7. Crop Recommendations (`/crop-recommendations`)
Personalized crop suggestions based on:
- Soil type
- Season (Kharif, Rabi, Zaid)
- Water availability
- Detailed information for rice, wheat, maize
- Yield and market price data

### 8. Farming Guide (`/farming-guide`)
Comprehensive agricultural information:
- Crop cultivation guides
- Irrigation best practices (drip, sprinkler, flood, rainwater harvesting)
- Pest and disease management
- Soil health management steps

### 9. Tutorials (`/tutorials`)
Educational video-style guides:
- Field preparation techniques
- Planting methods
- Harvest and post-harvest practices

## AI and Machine Learning Components

### Natural Language Processing
- **Google Gemini API**: Powers the chatbot assistant for answering farming questions
- Context-aware responses using user profile data
- Weather integration in conversations

### Computer Vision
- **Gemini 2.0 Vision Model**: Analyzes plant images for pest and disease identification
- Returns structured JSON data with identification, severity, and recommendations
- Fallback models for compatibility: `gemini-1.5-flash`, `gemini-pro-vision`

## Data Science Features

### Weather Analytics
- Real-time weather data from OpenWeatherMap API
- Historical data visualization using Chart.js
- Forecasting for agricultural planning
- Location-based services with ZIP code support for India

### Personalization
- User profile-based recommendations
- Historical conversation tracking
- Preference-based crop and farming suggestions

## Security Features

- **Row Level Security (RLS)**: Database policies ensuring users only access their own data
- **Session-based Authentication**: Secure login/logout mechanisms
- **JWT Token Management**: Supabase authentication handling
- **Password Protection**: Routes protected from unauthorized access

## UI/UX Features

- **Dark Theme Interface**: Optimized for farming environments
- **Responsive Design**: Works on all device sizes
- **Intuitive Navigation**: Sidebar with all features accessible
- **Real-time Updates**: Dynamic content loading
- **Visual Data Representation**: Charts, cards, and interactive elements
- **Accessibility**: Focus states and semantic HTML

## Installation and Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   OPENWEATHER_API_KEY=your_openweathermap_api_key
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
4. Run the application: `python app.py`

## Target Audience

- Indian farmers of all experience levels
- Agricultural students and researchers
- Farming cooperatives and organizations

## Special Features for Indian Agriculture

- ZIP code support for Indian postal codes
- Region-specific crop recommendations
- Local language support
- Government helpline integration
- Monsoon and seasonal farming guidance