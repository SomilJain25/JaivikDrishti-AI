
# 🌾 jaivikDrishti AI

**AI-Powered Agricultural Solutions for Modern Farming**

KrishiDrishti AI is a comprehensive platform that leverages artificial intelligence to revolutionize agriculture. Our platform provides farmers with cutting-edge tools for crop disease detection, market price prediction, yield estimation, and intelligent farming assistance.

## 🚀 Features

### 🌿 CropScan
- **AI Disease Detection**: Upload leaf images to instantly detect crop diseases
- **Visual Explanations**: Grad-CAM visualization shows exactly where the AI detected issues
- **Treatment Recommendations**: Get detailed treatment advice for identified diseases
- **Multi-Crop Support**: Supports Tomato, Potato, and other major crops

### 📈 MandiBazaar AI
- **Price Prediction**: Forecast crop prices based on location and market trends
- **Market Intelligence**: Get insights on best selling times and demand patterns
- **Multi-State Support**: Coverage across major agricultural states in India

### 🌾 YieldSense
- **Yield Estimation**: Predict crop yields using weather and soil data
- **Environmental Factors**: Considers temperature, rainfall, and soil type
- **Optimization Tips**: Receive recommendations for maximizing yields

### 🤖 KrishiBot
- **AI Assistant**: Natural language chatbot for farming queries
- **Expert Knowledge**: Access to comprehensive agricultural knowledge base
- **Multilingual Support**: Available in English and Hindi

## 🏗️ Architecture

```
KrishiDrishti-AI/
├── DrishtiScan/          # Backend API (FastAPI)
│   ├── app/
│   │   ├── main.py       # FastAPI application
│   │   └── predict.py    # ML prediction engine
│   ├── model/            # ML models and labels
│   ├── tests/            # API tests
│   └── requirements.txt  # Python dependencies
├── frontend/             # React Frontend (Vite)
│   ├── src/
│   │   ├── components/   # Reusable UI components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API integration
│   │   └── context/      # React context providers
│   ├── public/           # Static assets
│   └── package.json      # Node dependencies
└── README.md
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance async web framework
- **TensorFlow/Keras**: Deep learning for disease detection
- **Python**: Core programming language
- **Uvicorn**: ASGI server

### Frontend
- **React 19**: Modern JavaScript library
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icons

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd DrishtiScan
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   ```
   http://localhost:5173
   ```

## 📊 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/`

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Dataset**: PlantVillage dataset for disease detection training
- **Icons**: Lucide React for beautiful UI icons
- **UI Framework**: Tailwind CSS for responsive design

## 📞 Contact

- **Email**: contact@krishidrishti.ai
- **Website**: https://krishidrishti.ai
- **LinkedIn**: [KrishiDrishti AI](https://linkedin.com/company/krishidrishti-ai)

---

**Made with ❤️ for farmers, by developers who care about agriculture**
