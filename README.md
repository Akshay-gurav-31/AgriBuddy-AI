# 🌾 AgriBuddy - Smart Farming Assistant

> An intelligent agricultural assistant application designed to empower farmers with AI-driven crop recommendations, pest control solutions, weather insights, and comprehensive farming guidance.

---

## 📸 Application Screenshots

### Dashboard & Chat Interface
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/135aa37e-fa2a-4556-9ae1-17453309524c.jpg" width="250" alt="Chat Interface"/>
<br><sub>AI Chatbot Dashboard</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/15aaded2-1ede-4ff0-97dd-81a3f9e3c9d4.jpg" width="250" alt="Weather Dashboard"/>
<br><sub>Weather Dashboard</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/17677bda-24ea-4a92-bb31-6fd2faa21715.jpg" width="250" alt="Crop Analysis"/>
<br><sub>Crop Recommendations</sub>
</td>
</tr>
</table>

### Tools & Analysis Features
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/26b4b0f9-2787-4bc4-81d9-2394b5e415dc.jpg" width="250" alt="Pest Checker"/>
<br><sub>Pest Detection Tool</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/4e5ff42f-e2b2-462c-aa7c-e4f81fa69a88.jpg" width="250" alt="Soil Analysis"/>
<br><sub>Soil Analysis</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/50e430d0-cb09-477b-a10b-9aea4116c15b.jpg" width="250" alt="Pest Control"/>
<br><sub>Pest Control Guide</sub>
</td>
</tr>
</table>

### Additional Features
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/595c8e34-9df4-4b09-9c34-af5d7c385fea.jpg" width="250" alt="Farming Guide"/>
<br><sub>Farming Guide</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/6c210f84-9b24-4679-b3ab-4978348e204c.jpg" width="250" alt="Tutorials"/>
<br><sub>Educational Tutorials</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/9e320457-6ae2-4d8a-8ad7-422897e25d88.jpg" width="250" alt="Login"/>
<br><sub>Authentication</sub>
</td>
</tr>
</table>

### Mobile & User Experience
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/b2893932-2e03-430f-9147-92cab683a9ee.jpg" width="250" alt="Mobile View"/>
<br><sub>Responsive Design</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/d1a4c153-753d-41e5-9131-037c0be3817d.jpg" width="250" alt="User Profile"/>
<br><sub>User Profile</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/e5b59d96-cedd-4749-99cf-ae9d81b259eb.jpg" width="250" alt="Feature Menu"/>
<br><sub>Feature Navigation</sub>
</td>
</tr>
</table>

### Additional Interface
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/Akshay-gurav-31/AgriBuddy-AI/main/images/fa9c1777-95b1-4385-8a17-917a9286ac44.jpg" width="250" alt="Settings"/>
<br><sub>App Interface</sub>
</td>
</tr>
</table>

---

## 🛠️ Tech Stack

### Backend
- **Python Flask** - Web framework for building the application
- **Supabase** - Backend-as-a-Service (BaaS) for database and authentication
- **Google Generative AI (Gemini)** - AI models for chatbot and image analysis
- **OpenWeatherMap API** - Weather data and geocoding services

### Frontend
- **HTML/CSS/JavaScript** - Core frontend technologies
- **Chart.js** - Data visualization for weather analytics
- **Font Awesome** - Icon library for UI elements

### Database
- **PostgreSQL** - Relational database provided by Supabase
- **Row Level Security (RLS)** - Data isolation and security policies

---

## 🔑 Required API Keys

To run AgriBuddy successfully, you'll need to configure the following API keys:

**Google Generative AI (Gemini) API Key**
- Used for AI chat responses and pest/disease image analysis
- Model priority: `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-pro` → `gemini-1.5-pro`

**OpenWeatherMap API Key**
- Used for weather data and location-based services
- Provides real-time weather information and forecasts

**Supabase URL and Anon Key**
- Used for database operations and user authentication
- Provides secure access to PostgreSQL database

---

## 📊 Database Schema

The application utilizes three main PostgreSQL tables:

### Profiles Table
Comprehensive user profile information storage:
- `id` - UUID (Primary Key)
- `user_id` - Foreign key to auth.users
- `full_name` - User's full name
- `phone_number` - Contact information
- `state`, `city`, `region` - Location details
- `crops` - JSONB array of crops
- `land_area` and `land_unit` - Farm size information
- `past_cultivation`, `future_plans` - Farming history and plans
- `water_source`, `soil_type` - Farming conditions
- `current_crops`, `preferred_crops` - Crop preferences
- `preferred_language` - Language preference
- `created_at`, `updated_at` - Timestamps

### Conversations Table
Chat conversation metadata management:
- `id` - UUID (Primary Key)
- `created_at`, `updated_at` - Timestamps
- `title` - Conversation title
- `user_id` - Foreign key to user

### Messages Table
Individual chat message storage:
- `id` - UUID (Primary Key)
- `conversation_id` - Foreign key to conversations
- `role` - Message sender (user/assistant)
- `content` - Message content
- `created_at` - Timestamp

---

## 🎯 Application Features & Pages

### 🔐 Authentication System
**Login** (`/login`) - Secure user authentication with email and password
**Signup** (`/signup`) - New user registration with comprehensive profile creation
**Logout** (`/logout`) - Secure session termination

### 💬 Chat Interface (`/chat-interface`)
The central dashboard featuring:
- AI-powered farming assistant chatbot with advanced NLP
- Context-aware responses based on user profile and farming conditions
- Integrated weather data in conversations
- Complete message history storage and retrieval
- Location-based weather queries supporting city names and ZIP codes

### 🌤️ Weather Dashboard (`/weather-dashboard`)
Comprehensive weather analytics and insights:
- Real-time weather data for any location globally
- 5-day weather forecast with detailed predictions
- Temperature and precipitation visualization charts
- Climate statistics including temperature, humidity, and wind speed
- Real-time clock display with timezone support
- Responsive grid layout with multiple interactive data visualizations

### 🐛 Pest Checker (`/pest-checker`)
AI-powered pest and disease identification system:
- Image upload functionality for comprehensive plant photo analysis
- Computer vision analysis using Gemini 2.0 Vision model
- Accurate identification of pests, diseases, and other plant issues
- Severity assessment with affected crops information
- Customized solutions and prevention recommendations

### 🛡️ Pest Control Guide (`/pest-control`)
Integrated Pest Management (IPM) strategies and solutions:
- Biological control methods and natural predators
- Cultural practices and preventive measures
- Chemical control options with safety guidelines
- Monitoring and scouting techniques for early detection
- Comprehensive database of common pests and their solutions

### 🌱 Soil Analysis (`/soil-analysis`)
Detailed soil health assessment and improvement tool:
- Recommendations based on pH levels and organic matter content
- Ideal soil parameters for major Indian crops
- Comprehensive soil improvement and amendment guides

### 🌾 Crop Recommendations (`/crop-recommendations`)
Personalized crop suggestions powered by intelligent algorithms:
- Based on soil type, season (Kharif, Rabi, Zaid), and water availability
- Detailed cultivation information for rice, wheat, maize
- Yield projections and market price data analysis
- Region-specific recommendations

### 📚 Farming Guide (`/farming-guide`)
Comprehensive agricultural information and best practices:
- Step-by-step crop cultivation guides
- Irrigation techniques (drip, sprinkler, flood, rainwater harvesting)
- Advanced pest and disease management strategies
- Soil health management protocols and improvements

### 🎓 Tutorials (`/tutorials`)
Educational video-style guides and demonstrations:
- Field preparation techniques and equipment usage
- Optimal planting methods for different crops
- Harvest and post-harvest practices for maximum yield

---

## 🤖 AI and Machine Learning Components

### Natural Language Processing
- **Google Gemini API** - Powers the intelligent chatbot assistant
- Context-aware response generation using comprehensive user profile data
- Seamless weather integration in natural conversations

### Computer Vision
- **Gemini 2.0 Vision Model** - Analyzes plant images for pest and disease identification
- Structured JSON output with identification results, severity levels, and recommendations
- Fallback model support: `gemini-1.5-flash`, `gemini-pro-vision`

---

## 📈 Data Science Features

### Weather Analytics
- Real-time weather data acquisition from OpenWeatherMap API
- Historical data visualization and trend analysis using Chart.js
- Agricultural forecasting for informed planning and decision-making
- Advanced location-based services with ZIP code support for Indian regions

### Personalization Engine
- User profile-based intelligent recommendations
- Historical conversation tracking and analysis
- Preference-based crop and farming suggestions
- Continuous learning from user interactions

---

## 🔒 Security Features

- **Row Level Security (RLS)** - Database policies ensuring users access only their own data
- **Session-based Authentication** - Secure login and logout mechanisms
- **JWT Token Management** - Supabase authentication handling with secure tokens
- **Password Protection** - Routes protected from unauthorized access

---

## 🎨 UI/UX Features

- **Dark Theme Interface** - Optimized for extended use in farming environments
- **Responsive Design** - Seamless experience across all devices and screen sizes
- **Intuitive Navigation** - Sidebar with organized feature access
- **Real-time Updates** - Dynamic content loading and instant notifications
- **Visual Data Representation** - Interactive charts, cards, and graphical elements
- **Accessibility** - Proper focus states and semantic HTML structure

---

## ⚙️ Installation & Setup

**Step 1: Clone the Repository**
```bash
git clone https://github.com/Akshay-gurav-31/AgriBuddy-AI.git
cd AgriBuddy-AI
```

**Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 3: Configure Environment Variables**
Create a `.env` file in the project root and add:
```
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweathermap_api_key
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

**Step 4: Run the Application**
```bash
python app.py
```

---

## 👥 Target Audience

- **Indian Farmers** - All experience levels from beginners to experienced cultivators
- **Agricultural Students** - Learning practical farming techniques and science
- **Researchers** - Data-driven agricultural insights and analysis
- **Farming Cooperatives** - Organizational and group farming management
- **Agricultural Organizations** - Extension services and farmer support programs

---

## 🇮🇳 Special Features for Indian Agriculture

- **ZIP Code Support** - Full compatibility with Indian postal codes
- **Region-Specific Recommendations** - Tailored suggestions for different Indian regions
- **Local Language Support** - Accessibility in regional languages
- **Government Helpline Integration** - Links to official agricultural support services
- **Monsoon & Seasonal Guidance** - Specialized advice for Indian farming seasons (Kharif, Rabi, Zaid)

---

## 📄 License

This project is open source and available for agricultural and educational purposes.

## 🙌 Contributing

We welcome contributions from farmers, developers, and agricultural experts. Please feel free to submit issues and pull requests to improve AgriBuddy.

---

**Made with ❤️ for Indian Farmers**
