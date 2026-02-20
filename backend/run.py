import uvicorn
import os
import sys

# Add 'backend' to sys.path to allow running from root dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=True
    )
