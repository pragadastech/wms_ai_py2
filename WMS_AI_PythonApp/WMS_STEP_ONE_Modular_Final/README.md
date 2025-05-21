# Warehouse Management System (WMS)

A modern, FastAPI-based Warehouse Management System that integrates with NetSuite for comprehensive warehouse operations management. This system provides a robust solution for managing warehouse inventory, bin locations, and seamless integration with NetSuite ERP.

## 🌟 Key Features

### Authentication & Security
- **JWT-based Authentication**: Secure token-based authentication system
- **Role-based Access Control**: Different access levels for admin and regular users
- **Password Hashing**: Secure password storage using bcrypt
- **CORS Protection**: Configured for specific origins

### NetSuite Integration
- **Real-time Data Sync**: Synchronize inventory data with NetSuite
- **Item Management**: Fetch and update item details
- **Transaction History**: Track all warehouse transactions
- **Error Handling**: Robust error handling for API failures

### Inventory Management
- **Stock Tracking**: Real-time inventory level monitoring
- **Item Location**: Track item locations within the warehouse
- **Stock Movement**: Record and track stock movements
- **Inventory Reports**: Generate detailed inventory reports

### Bin Management
- **Location Tracking**: Efficient bin location management
- **Space Optimization**: Optimize warehouse space utilization
- **Bin Assignment**: Automated and manual bin assignment
- **Bin History**: Track bin usage and movement history

### Admin Features
- **User Management**: Create, update, and manage user accounts
- **System Configuration**: Configure system-wide settings
- **Access Control**: Manage user permissions and roles
- **Audit Logs**: Track system activities and changes

## 🛠️ Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.9+)
- **Authentication**: JWT with Python-Jose
- **Database**: Supabase (PostgreSQL)
- **API Integration**: NetSuite REST API
- **Containerization**: Docker
- **Documentation**: Swagger UI & ReDoc

### Project Structure
```
WMS_STEP_ONE_Modular_Final/
├── app/
│   ├── routes/
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── admin.py        # Admin operations
│   │   ├── user.py         # User operations
│   │   ├── netsuite.py     # NetSuite integration
│   │   └── bin_management.py # Bin management
│   ├── middleware/
│   │   └── exception_handler.py # Global exception handling
│   └── main.py            # Application entry point
├── chat/                  # Chat functionality
├── Data/                  # Data storage
├── utils/                 # Utility functions
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## 📋 System Requirements

### Hardware Requirements
- CPU: 2+ cores
- RAM: 4GB minimum
- Storage: 10GB minimum

### Software Requirements
- Python 3.9 or higher
- Docker (optional)
- NetSuite account with API access
- Supabase account
- Modern web browser

## 🔧 Installation Guide

### 1. Clone the Repository
```bash
git clone [repository-url]
cd WMS_STEP_ONE_Modular_Final
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/MacOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# NetSuite Configuration
NETSUITE_ACCOUNT_ID=your_netsuite_account_id
NETSUITE_CONSUMER_KEY=your_netsuite_consumer_key
NETSUITE_CONSUMER_SECRET=your_netsuite_consumer_secret
NETSUITE_TOKEN_ID=your_netsuite_token_id
NETSUITE_TOKEN_SECRET=your_netsuite_token_secret

# Application Configuration
APP_ENV=development  # or production
DEBUG=True
```

## 🚀 Deployment

### Local Development
```bash
uvicorn app.main:app --reload --port 8000
```

### Docker Deployment
```bash
# Build the Docker image
docker build -t wms-app .

# Run the container
docker run -d -p 8000:8000 --name wms-container wms-app
```

### Production Deployment
1. Set up a production environment
2. Configure SSL certificates
3. Set up a reverse proxy (e.g., Nginx)
4. Configure environment variables
5. Deploy using Docker or direct Python installation

## 📚 API Documentation

### Accessing Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Endpoints

#### Authentication
```bash
POST /token
Content-Type: application/json
{
    "username": "your_username",
    "password": "your_password"
}
```

#### Protected Endpoints
```bash
GET /api/v1/items
Authorization: Bearer your_token_here
```

## 🔐 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use secure, unique passwords
   - Rotate API keys regularly

2. **Authentication**
   - Use strong passwords
   - Implement rate limiting
   - Enable 2FA where possible

3. **Data Protection**
   - Encrypt sensitive data
   - Regular backups
   - Access logging

## 🐛 Troubleshooting

### Common Issues

1. **Connection Issues**
   - Check network connectivity
   - Verify API credentials
   - Check firewall settings

2. **Authentication Problems**
   - Verify JWT token
   - Check user credentials
   - Validate token expiration

3. **NetSuite Integration**
   - Verify API credentials
   - Check rate limits
   - Validate data format

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

### Code Standards
- Follow PEP 8 guidelines
- Write unit tests
- Document new features
- Update documentation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- NetSuite for their comprehensive API
- FastAPI for the excellent framework
- Supabase for the database infrastructure
- All contributors and maintainers

## 📞 Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed
4. Contact the development team

## 🔄 Updates and Maintenance

- Regular security updates
- Performance optimizations
- New feature additions
- Bug fixes and patches 