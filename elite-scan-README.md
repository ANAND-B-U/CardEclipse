# EliteScan Pro - Business Card OCR System

A premium business card OCR application with advanced AI-powered text extraction and professional data export capabilities.

## 🌟 Features

- **AI-Powered OCR**: Extract contact information from business cards using NVIDIA AI
- **Premium UI**: Professional black, gold, and purple theme with dazzling effects
- **Multiple Formats**: Support for images (JPG, PNG) and PDF files
- **Batch Processing**: Process multiple business cards simultaneously
- **Data Export**: Export extracted data to CSV and Excel formats
- **Real-time Processing**: Fast and accurate text extraction
- **Professional Results**: Clean, structured data output

## 🚀 Quick Start

### Prerequisites

- Python 3.14+
- NVIDIA API Key (for AI processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd business-card-ocr
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your NVIDIA_API_KEY
   ```

4. **Start Backend Server**
   ```bash
   python app.py
   ```

5. **Start Frontend**
   ```bash
   cd ../frontend
   # Open index.html in your browser or serve with a web server
   ```

## 📁 Project Structure

```
business-card-ocr/
├── README.md               # Main project documentation
├── .gitignore             # Git ignore file
├── backend/               # Flask backend application
│   ├── app.py            # Main Flask application
│   ├── requirements.txt  # Python dependencies
│   ├── .env.example      # Environment variables template
│   ├── .env             # Environment variables (create from .env.example)
│   └── temp/            # Temporary file storage
└── frontend/             # Premium frontend application
    ├── index.html        # Main frontend HTML
    ├── styles.css        # Premium styling with gold effects
    ├── script.js         # Frontend JavaScript logic
    └── README.md         # Frontend documentation
```

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the backend directory:

```env
# API Keys
NVIDIA_API_KEY=your_nvidia_api_key_here

# Server Configuration
FLASK_ENV=development
```

### Getting NVIDIA API Key

1. Visit [NVIDIA NGC](https://ngc.nvidia.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Generate a new API key
5. Add the key to your `.env` file

## 🎯 Usage

### Single Card Processing

1. Open the frontend in your browser
2. Drag and drop a business card image or click to select
3. Choose AI model (NVIDIA recommended)
4. Click "Scan Cards" to process
5. View extracted information
6. Download results as CSV or Excel

### Batch Processing

1. Select "Batch Processing" mode
2. Upload multiple business card images
3. Click "Scan Cards" to process all cards
4. Review individual results
5. Export all data to CSV or Excel

### Supported File Formats

- **Images**: JPG, JPEG, PNG
- **Documents**: PDF
- **Size Limit**: 50MB per file

## 📊 Data Export

### CSV Export
- Structured data with headers
- All extracted fields included
- Compatible with Excel and spreadsheet applications

### Excel Export
- Professional Excel-compatible format
- Formatted for easy data analysis
- Includes all contact information fields

### Exported Fields

- Name
- Title
- Company
- Email
- Phone Numbers (multiple)
- Website
- Address
- Tokens Used
- AI Model Used
- Original Filename

## 🛠️ API Endpoints

### Backend API

- `GET /` - API information and status
- `GET /health` - Health check endpoint
- `POST /api/single` - Process single business card
- `POST /api/batch` - Process multiple business cards
- `POST /api/download/csv` - Download CSV export
- `POST /api/download/excel` - Download Excel export

### Request Format

**Single Card:**
```javascript
const formData = new FormData();
formData.append('image', file);
formData.append('model', 'nvidia');
```

**Batch Processing:**
```javascript
const formData = new FormData();
formData.append('images', file1);
formData.append('images', file2);
formData.append('model', 'nvidia');
```

## 🎨 Frontend Features

### Premium UI Elements

- **Gold Dazzling Effects**: Animated gold shimmer and glow
- **Glass Morphism**: Modern glass-like card designs
- **Responsive Design**: Works on all screen sizes
- **Dark Theme**: Professional black, gold, and purple color scheme
- **Smooth Animations**: Premium transitions and hover effects

### Interactive Components

- **Drag & Drop Upload**: Intuitive file upload interface
- **Real-time Processing**: Live feedback during OCR processing
- **Result Display**: Professional card-based result presentation
- **Download Options**: One-click CSV and Excel export

## 🔍 AI Models

### NVIDIA Phi-3.5 Vision

- **Model**: `microsoft/phi-3.5-vision-instruct`
- **Provider**: NVIDIA API
- **Specialization**: Vision and text understanding
- **Performance**: Fast and accurate OCR processing

## 📋 Requirements

### Backend Dependencies

```
Flask==3.0.0
flask-cors==4.0.0
openai==1.54.0
Pillow==12.1.0
python-dotenv==1.0.0
phonenumbers==8.13.27
```

### System Requirements

- **Python**: 3.14+
- **Memory**: 4GB+ RAM recommended
- **Storage**: 100MB+ available space
- **Network**: Internet connection for AI API calls

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure NVIDIA_API_KEY is correctly set in `.env`
   - Verify API key is valid and active
   - Check internet connection

2. **File Upload Issues**
   - Check file size (max 50MB)
   - Verify supported file formats
   - Ensure file is not corrupted

3. **Processing Errors**
   - Check backend logs for detailed error messages
   - Verify image quality and clarity
   - Try different AI model if available

4. **Download Issues**
   - Ensure you have successful results before downloading
   - Check browser download settings
   - Verify file permissions

### Debug Mode

Enable debug mode by setting `FLASK_ENV=development` in `.env` file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## 🎯 Future Enhancements

- [ ] Additional AI model support
- [ ] Advanced data validation
- [ ] Cloud storage integration
- [ ] Mobile application
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard

---

**EliteScan Pro** - Professional Business Card OCR with Premium AI Technology