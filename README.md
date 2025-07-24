# Course Availability Notifier 🎓

A professional, modular Python application that monitors **Ontario Tech University** course availability and sends SMS notifications when spots become available. Built with Selenium for web scraping, Twilio for SMS notifications, and APScheduler for automated monitoring.

## Features ✨

- 🔍 **Automated Course Monitoring**: Continuously checks course availability at configurable intervals
- 📱 **SMS Notifications**: Instant alerts via Twilio when courses become available
- 🌐 **Web Scraping**: Uses Selenium with Chrome for reliable course data extraction
- ⚙️ **Configurable**: Easy configuration via environment variables
- 📊 **Comprehensive Logging**: Detailed logging with configurable levels
- 🐳 **Docker Support**: Ready-to-deploy containerized solution
- 🔄 **Graceful Shutdown**: Proper resource cleanup and signal handling
- 🛡️ **Error Handling**: Robust error handling and recovery mechanisms

## Quick Start 🚀

### Prerequisites

- Python 3.8+ installed
- Chrome/Chromium browser installed
- Twilio account for SMS notifications
- University course registration system access

### Installation

1. **Clone and setup the project**:

```bash
git clone <your-repo-url>
cd course_enrollment_notifer
```

2. **Configure environment variables**:

```bash
# Copy the example environment file
cp env.example .env

# Edit the configuration (see Configuration section below)
nano .env  # or use your preferred editor
```

3. **Run the application**:

**On Linux/macOS:**

```bash
chmod +x run.sh
./run.sh
```

**On Windows:**

```cmd
run.bat
```

**Or manually:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Configuration ⚙️

### Required Environment Variables

Copy `env.example` to `.env` and configure the following:

#### Twilio Configuration (Required)

```env
TWILIO_SID=your_twilio_account_sid_here
TWILIO_TOKEN=your_twilio_auth_token_here
TWILIO_FROM=+1234567890  # Your Twilio phone number
TWILIO_TO=+1987654321    # Your phone number to receive notifications
```

#### Course Configuration (Required)

```env
COURSE_CODES=CSCI4020U,CSCI3540U,CSCI2450U  # Comma-separated course codes (Ontario Tech format)
INTERVAL_MIN=15  # Check interval in minutes
```

#### Site Configuration (Ontario Tech University)

```env
BASE_URL
SITE_USERNAME=your_ontario_tech_username  # Required for login
SITE_PASSWORD=your_ontario_tech_password  # Required for login
```

#### Browser Configuration (Optional)

```env
CHROME_PROFILE_PATH=./chrome_profile  # Chrome profile directory
HEADLESS=true  # Run browser in headless mode
```

#### Logging Configuration (Optional)

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=course_notifier.log  # Log file path
```

### Getting Twilio Credentials

1. Sign up for a free account at [twilio.com](https://www.twilio.com)
2. Get your Account SID and Auth Token from the Twilio Console
3. Purchase a phone number or use the trial number for testing
4. Add your personal phone number to receive notifications

## Usage 📖

### Basic Usage

1. Configure your `.env` file with Twilio credentials and course codes
2. Run the application using one of the startup scripts
3. The application will:
   - Check course availability immediately
   - Continue monitoring at the specified interval
   - Send SMS notifications when spots become available
   - Log all activities to console and log file

### Customizing for Your University

The scraper is designed to be easily customizable for different university systems. You'll need to modify:

1. **URL Structure** in `config.py`:

   - Update `BASE_URL` to match your university's course search URL
   - Modify `format_course_url()` in `utils.py` if needed

2. **HTML Parsing** in `scraper.py`:

   - Update the `check_course()` method to match your university's HTML structure
   - Modify the regex patterns for extracting seat availability

3. **Login Process** (if required):
   - Update the `login_if_needed()` method with correct selectors
   - Provide login credentials in environment variables

### Example Course Code Formats

Different universities use different course code formats:

```env
# Examples for different institutions
COURSE_CODES=CSCI3540U,MATH1001U          # University of Ontario
COURSE_CODES=CS101,MATH205,PHYS301        # Generic format
COURSE_CODES=COMP-SCI-101,MATH-205        # Hyphenated format
```

## Docker Deployment 🐳

### Using Docker Compose (Recommended)

1. **Build and run**:

```bash
# Make sure your .env file is configured
docker-compose up -d
```

2. **View logs**:

```bash
docker-compose logs -f course-notifier
```

3. **Stop the service**:

```bash
docker-compose down
```

### Using Docker directly

1. **Build the image**:

```bash
docker build -t course-notifier .
```

2. **Run the container**:

```bash
docker run -d --name course-notifier \
  --env-file .env \
  -v $(pwd)/chrome_profile:/app/chrome_profile \
  -v $(pwd)/logs:/app/logs \
  course-notifier
```

## Linux Service Setup 🛠️

To run as a system service on Linux:

1. **Update the service file**:

```bash
# Edit course-notifier.service
nano course-notifier.service

# Update these paths:
# - User=your_username
# - WorkingDirectory=/path/to/your/course_checker
# - ExecStart=/path/to/your/course_checker/venv/bin/python /path/to/your/course_checker/main.py
```

2. **Install and start the service**:

```bash
sudo cp course-notifier.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable course-notifier
sudo systemctl start course-notifier
```

3. **Monitor the service**:

```bash
sudo systemctl status course-notifier
sudo journalctl -u course-notifier -f
```

## Architecture 🏗️

The application follows a modular architecture:

```
course_enrollment_notifer/
├── config.py          # Configuration and environment variables
├── utils.py           # Utility functions and logging setup
├── scraper.py         # Web scraping with Selenium
├── notifier.py        # SMS notifications with Twilio
├── scheduler.py       # Job scheduling and main orchestration
├── main.py           # Application entry point
├── requirements.txt   # Python dependencies
├── env.example       # Environment variables template
├── run.sh           # Unix startup script
├── run.bat          # Windows startup script
├── Dockerfile       # Docker container definition
└── docker-compose.yml # Docker Compose configuration
```

### Key Components

- **CourseScraper**: Handles web scraping with Selenium and Chrome
- **NotificationService**: Manages Twilio SMS notifications with duplicate prevention
- **CourseMonitor**: Orchestrates the monitoring process with APScheduler
- **Configuration**: Centralized configuration management with validation

## Troubleshooting 🔧

### Common Issues

1. **Chrome/ChromeDriver Issues**:

   ```bash
   # Update Chrome and ChromeDriver
   # Make sure they're compatible versions
   ```

2. **Twilio Authentication Errors**:

   ```bash
   # Verify your SID and Auth Token
   # Check account balance for paid accounts
   # Verify phone numbers are properly formatted
   ```

3. **Course Not Found**:

   ```bash
   # Check course code format
   # Verify the university's URL structure
   # Test manual navigation to course pages
   ```

4. **Login Issues**:
   ```bash
   # Use Chrome profile to maintain login sessions
   # Update selectors in login_if_needed() method
   # Consider manual login via Chrome profile
   ```

### Debugging

1. **Enable Debug Logging**:

   ```env
   LOG_LEVEL=DEBUG
   ```

2. **Run in Non-Headless Mode**:

   ```env
   HEADLESS=false
   ```

3. **Check Logs**:
   ```bash
   tail -f course_notifier.log
   ```

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Customization Guidelines

When adapting for different universities:

- Keep the modular architecture
- Update configuration rather than hardcoding values
- Add proper error handling
- Test with various course scenarios
- Document any university-specific requirements

## Security Notes 🔒

- Store sensitive credentials in `.env` file only
- Never commit credentials to version control
- Use environment variables in production
- Consider using Chrome profile for persistent login
- Regularly update dependencies for security patches

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Support 💬

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue with detailed information
4. Include your configuration (without credentials)

---

**Disclaimer**: This tool is for educational purposes. Ensure compliance with your university's terms of service and rate limiting policies. Use responsibly and respectfully.
